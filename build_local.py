"""Build a personal-test APK using an installed Android SDK and JDK or Eclipse ECJ.

Python 3.8+. No downloads are performed. Set ANDROID_PLATFORM_JAR and
ANDROID_BUILD_TOOLS to installed SDK paths. If javac is unavailable, set
JAVA_COMPILER_JAR to an Eclipse ECJ compiler jar. A reusable test signing key is
generated in signing/ on the first run. Do not use this key for a public release.
"""
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'build-local'
OUT.mkdir(exist_ok=True)
PLATFORM = Path(os.environ['ANDROID_PLATFORM_JAR']).resolve()
TOOLS = Path(os.environ['ANDROID_BUILD_TOOLS']).resolve()
SRC = ROOT / 'app/src/main'

def run(*args):
    subprocess.run([str(x) for x in args], check=True, cwd=ROOT)

for name in ('aapt2', 'd8', 'zipalign', 'apksigner'):
    if os.name != 'nt':
        (TOOLS / name).chmod(0o755)

generated, classes, dex = (OUT / n for n in ('generated', 'classes', 'dex'))
for folder in (generated, classes, dex):
    if folder.exists(): shutil.rmtree(folder)
    folder.mkdir()

manifest = (SRC / 'AndroidManifest.xml').read_text()
manifest = manifest.replace('<manifest ', '<manifest package="app.topnote.personal" ', 1)
(OUT / 'AndroidManifest.xml').write_text(manifest)
run(TOOLS / 'aapt2', 'compile', '--dir', SRC / 'res', '-o', OUT / 'resources.zip')
run(TOOLS / 'aapt2', 'link', '-o', OUT / 'unsigned.apk', '-I', PLATFORM,
    '--manifest', OUT / 'AndroidManifest.xml', '--java', generated,
    '--min-sdk-version', '26', '--target-sdk-version', '34', OUT / 'resources.zip')
sources = list((SRC / 'java').rglob('*.java')) + list(generated.rglob('*.java'))
bootclasspath = str(PLATFORM) + os.pathsep + str(TOOLS / 'core-lambda-stubs.jar')
if shutil.which('javac'):
    run('javac', '-source', '8', '-target', '8', '-bootclasspath', bootclasspath, '-encoding', 'UTF-8', '-d', classes, *sources)
else:
    run('java', '-jar', os.environ['JAVA_COMPILER_JAR'], '-source', '8', '-target', '8',
        '-proc:none', '-bootclasspath', bootclasspath, '-encoding', 'UTF-8', '-d', classes, *sources)
with zipfile.ZipFile(OUT / 'classes.jar', 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in classes.rglob('*.class'): archive.write(file, file.relative_to(classes))
run(TOOLS / 'd8', '--lib', PLATFORM, '--min-api', '26', '--output', dex, OUT / 'classes.jar')
with zipfile.ZipFile(OUT / 'unsigned.apk', 'a', zipfile.ZIP_DEFLATED) as archive:
    for file in dex.glob('*.dex'): archive.write(file, file.name)
run(TOOLS / 'zipalign', '-f', '4', OUT / 'unsigned.apk', OUT / 'aligned.apk')
key = ROOT / 'signing/topnote-test.p12'
key.parent.mkdir(exist_ok=True)
if not key.exists():
    run('keytool', '-genkeypair', '-keystore', key, '-storetype', 'PKCS12', '-storepass', 'android',
        '-keypass', 'android', '-alias', 'androiddebugkey', '-keyalg', 'RSA', '-keysize', '2048',
        '-validity', '10000', '-dname', 'CN=Android Debug,O=TopNote Personal,C=US')
apk = OUT / 'TopNote-1.3.apk'
run(TOOLS / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'androiddebugkey',
    '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--out', apk, OUT / 'aligned.apk')
run(TOOLS / 'apksigner', 'verify', '--verbose', apk)
print('APK:', apk)
