"""Run the real service/receiver against a small fake Android host (no device).

Requires Java and either javac or JAVA_COMPILER_JAR (Eclipse ECJ).
These tests check lifecycle logic, not Android/OEM integration or rendering.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
STUBS = {
'android/content/SharedPreferences.java': '''package android.content;
import java.util.*;
public class SharedPreferences {
 public final Map<String,Object> values=new HashMap<>();
 public boolean getBoolean(String k,boolean d){return (Boolean)values.getOrDefault(k,d);}
 public int getInt(String k,int d){return (Integer)values.getOrDefault(k,d);}
 public long getLong(String k,long d){return (Long)values.getOrDefault(k,d);}
 public String getString(String k,String d){return (String)values.getOrDefault(k,d);}
 public boolean contains(String k){return values.containsKey(k);}
 public Editor edit(){return new Editor();}
 public class Editor {
  public Editor putBoolean(String k,boolean v){values.put(k,v);return this;}
  public Editor putInt(String k,int v){values.put(k,v);return this;}
  public Editor putLong(String k,long v){values.put(k,v);return this;}
  public Editor putString(String k,String v){values.put(k,v);return this;}
  public Editor remove(String k){values.remove(k);return this;}
  public void apply(){} public boolean commit(){return true;}
 }
}''',
'android/content/Context.java': '''package android.content;
import android.app.*;import android.os.*;import android.view.*;import android.content.res.*;
public class Context {
 public static final int MODE_PRIVATE=0,RECEIVER_NOT_EXPORTED=4;
 public static final String WINDOW_SERVICE="window",ALARM_SERVICE="alarm";
 public static SharedPreferences prefs,diagnostics;public static WindowManager windows;
 public static PowerManager power;public static KeyguardManager keyguard;
 public static AlarmManager alarms;public static NotificationManager notifications;
 public static BroadcastReceiver receiver;public static int startCalls;public static Intent lastStart;
 public static boolean denyStart,overlay;
 public static void reset(){prefs=new SharedPreferences();diagnostics=new SharedPreferences();windows=new WindowManager();
  power=new PowerManager();keyguard=new KeyguardManager();alarms=new AlarmManager();notifications=new NotificationManager();
  receiver=null;startCalls=0;lastStart=null;denyStart=false;overlay=true;
  Handler.clear();SystemClock.reset();ActivityManager.exits.clear();ActivityManager.failHistory=false;
  PendingIntent.registry.clear();android.hardware.display.DisplayManager.listener=null;
 }
 public Context getApplicationContext(){return this;}
 public SharedPreferences getSharedPreferences(String n,int m){return "diagnostics".equals(n)?diagnostics:prefs;}
 public String getPackageName(){return "app.topnote.personal";}
 public Object getSystemService(String n){return ALARM_SERVICE.equals(n)?alarms:windows;}
 public <T>T getSystemService(Class<T> c){
  if(c==PowerManager.class)return c.cast(power);
  if(c==KeyguardManager.class)return c.cast(keyguard);
  if(c==NotificationManager.class)return c.cast(notifications);
  if(c==AlarmManager.class)return c.cast(alarms);
  if(c==ActivityManager.class)return c.cast(new ActivityManager());
  if(c==android.hardware.display.DisplayManager.class)return c.cast(new android.hardware.display.DisplayManager());
  throw new IllegalArgumentException("Unsupported service "+c);
 }
 public Resources getResources(){return new Resources();}
 public void registerReceiver(BroadcastReceiver r,IntentFilter f){receiver=r;}
 public void registerReceiver(BroadcastReceiver r,IntentFilter f,int flags){receiver=r;}
 public void unregisterReceiver(BroadcastReceiver r){if(receiver==r)receiver=null;}
 public void startForegroundService(Intent i){if(denyStart)throw new IllegalStateException();startCalls++;lastStart=i;}
}''',
'android/content/Intent.java': '''package android.content;public class Intent {
 public static final String ACTION_SCREEN_OFF="off",ACTION_SCREEN_ON="on",ACTION_USER_PRESENT="unlock",
 ACTION_BOOT_COMPLETED="boot",ACTION_MY_PACKAGE_REPLACED="update";
 public Class<?> target;private String action,packageName;
 public Intent(Context c,Class<?> k){target=k;}public Intent(String a){action=a;}
 public String getAction(){return action;}public Intent setAction(String a){action=a;return this;}
 public Intent setPackage(String p){packageName=p;return this;}public String getPackage(){return packageName;}
}''',
'android/content/IntentFilter.java': '''package android.content; public class IntentFilter {public void addAction(String a){}}''',
'android/content/BroadcastReceiver.java': '''package android.content; public abstract class BroadcastReceiver {public abstract void onReceive(Context c,Intent i);}''',
'android/content/pm/ServiceInfo.java': '''package android.content.pm; public class ServiceInfo {public static final int FOREGROUND_SERVICE_TYPE_SPECIAL_USE=1073741824;}''',
'android/content/res/Configuration.java': '''package android.content.res; public class Configuration {}''',
'android/content/res/Resources.java': '''package android.content.res; public class Resources {public android.util.DisplayMetrics getDisplayMetrics(){return new android.util.DisplayMetrics();}}''',
'android/util/DisplayMetrics.java': '''package android.util; public class DisplayMetrics {public float density=1;public int widthPixels=1080;}''',
'android/util/Log.java': '''package android.util; public class Log {public static int w(String a,String b,Throwable e){return 0;}}''',
'android/app/Service.java': '''package android.app;import android.content.*;import android.os.*;import android.content.res.*;
public class Service extends Context {
 public static final int START_STICKY=1,START_NOT_STICKY=2,STOP_FOREGROUND_REMOVE=1;
 public boolean foreground,stopped,failForeground;
 public void onCreate(){}public int onStartCommand(Intent i,int f,int id){return 0;}
 public void onConfigurationChanged(Configuration c){}public void onDestroy(){}public IBinder onBind(Intent i){return null;}
 public void startForeground(int id,Notification n){if(failForeground)throw new IllegalStateException();foreground=true;notifications.active=true;}
 public void startForeground(int id,Notification n,int type){startForeground(id,n);}
 public void stopForeground(int f){foreground=false;notifications.active=false;}public void stopSelf(){stopped=true;}
}''',
'android/app/KeyguardManager.java': '''package android.app; public class KeyguardManager {public boolean locked; public boolean isKeyguardLocked(){return locked;}}''',
'android/app/NotificationManager.java': '''package android.app;
public class NotificationManager {
 public static final int IMPORTANCE_LOW=2;public boolean allowed=true,active;public NotificationChannel channel;
 public void createNotificationChannel(NotificationChannel c){channel=c;}
 public boolean areNotificationsEnabled(){return allowed;}
 public NotificationChannel getNotificationChannel(String s){return channel;}
 public android.service.notification.StatusBarNotification[] getActiveNotifications(){return active
  ?new android.service.notification.StatusBarNotification[]{new android.service.notification.StatusBarNotification(1)}
  :new android.service.notification.StatusBarNotification[0];}
}''',
'android/app/NotificationChannel.java': '''package android.app;public class NotificationChannel {
 private int importance;public NotificationChannel(String id,String name,int level){importance=level;}
 public int getImportance(){return importance;}
 public void setDescription(String s){}public void setShowBadge(boolean b){}
}''',
'android/app/PendingIntent.java': '''package android.app;import android.content.*;import java.util.*;
public class PendingIntent {
 public static final int FLAG_UPDATE_CURRENT=1,FLAG_IMMUTABLE=2,FLAG_NO_CREATE=4;
 public static final Map<String,PendingIntent> registry=new HashMap<>();
 public Intent intent;public int flags;private String key;
 private static PendingIntent get(String type,int r,Intent i,int f){String k=type+":"+r+":"+i.target+":"+i.getAction();
  PendingIntent p=registry.get(k);if(p==null&&(f&FLAG_NO_CREATE)!=0)return null;
  if(p==null){p=new PendingIntent();p.key=k;registry.put(k,p);}p.intent=i;p.flags=f;return p;}
 public static PendingIntent getActivity(Context c,int r,Intent i,int f){return get("activity",r,i,f);}
 public static PendingIntent getService(Context c,int r,Intent i,int f){return get("service",r,i,f);}
 public static PendingIntent getBroadcast(Context c,int r,Intent i,int f){return get("broadcast",r,i,f);}
 public void cancel(){registry.remove(key);}
}''',
'android/app/Notification.java': '''package android.app; import android.content.*; public class Notification {
 public static final String CATEGORY_SERVICE="service"; public static final int VISIBILITY_PRIVATE=0;
 public static class Builder {
  public Builder(Context c,String id){} public Builder setSmallIcon(int i){return this;}
  public Builder setContentTitle(String s){return this;} public Builder setContentText(String s){return this;}
  public Builder setContentIntent(PendingIntent p){return this;} public Builder setOngoing(boolean b){return this;}
  public Builder setOnlyAlertOnce(boolean b){return this;}public Builder setCategory(String s){return this;}
  public Builder setVisibility(int v){return this;}public Builder addAction(Action a){return this;}
  public Notification build(){return new Notification();}
 }
 public static class Action {public static class Builder {
  public Builder(Object i,String s,PendingIntent p){}public Action build(){return new Action();}
 }}
}''',
'android/os/Build.java': '''package android.os; public class Build {public static final String MANUFACTURER="Test",MODEL="Phone";public static class VERSION {public static int SDK_INT=34;public static final String RELEASE="14";}}''',
'android/os/PowerManager.java': '''package android.os;public class PowerManager {
 public boolean interactive=true,exempt=true,saver,idle;
 public boolean isInteractive(){return interactive;}
 public boolean isIgnoringBatteryOptimizations(String p){return exempt;}
 public boolean isPowerSaveMode(){return saver;}public boolean isDeviceIdleMode(){return idle;}
}''',
'android/os/IBinder.java': '''package android.os; public interface IBinder {}''',
'android/os/Looper.java': '''package android.os; public class Looper {public static Looper getMainLooper(){return new Looper();}}''',
'android/os/Handler.java': '''package android.os;import java.util.*;import android.content.Context;
public class Handler {
 public static final List<Runnable> queue=new ArrayList<>();
 private static final Map<Runnable,Long> due=new IdentityHashMap<>();
 public Handler(Looper l){}public static void clear(){queue.clear();due.clear();}
 public void removeCallbacks(Runnable r){while(queue.remove(r)){}due.remove(r);}
 public void post(Runnable r){queue.add(r);due.put(r,SystemClock.uptimeMillis());}
 public void postDelayed(Runnable r,long delay){if(delay<=0)throw new AssertionError("busy loop");queue.add(r);due.put(r,SystemClock.uptimeMillis()+delay);}
 public static void next(){
  if(queue.isEmpty())throw new AssertionError("missing recovery callback");
  Context.windows.renderFrames();Runnable r=queue.remove(0);Long when=due.remove(r);
  if(when!=null&&when>SystemClock.uptimeMillis())SystemClock.advance(when-SystemClock.uptimeMillis());
  r.run();Context.windows.renderFrames();
 }
}''',
'android/provider/Settings.java': '''package android.provider; public class Settings {public static boolean canDrawOverlays(android.content.Context c){return android.content.Context.overlay;}}''',
'android/graphics/Color.java': '''package android.graphics; public class Color {public static final int WHITE=-1,BLACK=0xff000000;public static int rgb(int a,int b,int c){return 0;}}''',
'android/graphics/PixelFormat.java': '''package android.graphics; public class PixelFormat {public static final int TRANSLUCENT=-3;}''',
'android/graphics/Typeface.java': '''package android.graphics; public class Typeface {public static final Typeface DEFAULT=new Typeface();public static final int BOLD=1,NORMAL=0;}''',
'android/graphics/drawable/GradientDrawable.java': '''package android.graphics.drawable; public class GradientDrawable {public void setColor(int c){}public void setCornerRadius(int r){}}''',
'android/text/TextUtils.java': '''package android.text; public class TextUtils {public static class TruncateAt {public static final TruncateAt END=new TruncateAt();}}''',
'android/view/Gravity.java': '''package android.view; public class Gravity {public static final int TOP=48,LEFT=3,RIGHT=5,CENTER_HORIZONTAL=1;}''',
'android/view/View.java': '''package android.view;import android.graphics.*;
public class View {
 public static final int VISIBLE=0,INVISIBLE=4,GONE=8;
 public boolean attached,shown=true,invalidated;public int visibility=VISIBLE,windowVisibility=VISIBLE;
 public WindowManager.LayoutParams layout;
 public boolean isAttachedToWindow(){return attached;}
 public boolean isShown(){return attached&&shown&&visibility==VISIBLE;}
 public int getVisibility(){return visibility;}public void setVisibility(int v){visibility=v;if(v==VISIBLE)invalidated=true;}
 public int getWindowVisibility(){return windowVisibility;}
 public WindowManager.LayoutParams getLayoutParams(){return layout;}
 public void requestLayout(){invalidated=true;}public void invalidate(){invalidated=true;}
 public int getWidth(){return attached?300:0;}public int getHeight(){return attached?40:0;}
 public boolean getGlobalVisibleRect(Rect r){return isShown()&&windowVisibility==VISIBLE;}
 public void draw(Canvas c){onDraw(c);}protected void onDraw(Canvas c){}
}''',
'android/view/Display.java': '''package android.view;public class Display {public static final int DEFAULT_DISPLAY=0;}''',
'android/hardware/display/DisplayManager.java': '''package android.hardware.display;public class DisplayManager {
 public static DisplayListener listener;
 public interface DisplayListener {void onDisplayAdded(int id);void onDisplayRemoved(int id);void onDisplayChanged(int id);}
 public void registerDisplayListener(DisplayListener l,android.os.Handler h){listener=l;}
 public void unregisterDisplayListener(DisplayListener l){if(listener==l)listener=null;}
}''',
'android/app/ActivityManager.java': '''package android.app;import java.util.*;
public class ActivityManager {
 public static final List<ApplicationExitInfo> exits=new ArrayList<>();public static boolean failHistory;
 public List<ApplicationExitInfo> getHistoricalProcessExitReasons(String p,int pid,int max){if(failHistory)throw new SecurityException();return new ArrayList<>(exits.subList(0,Math.min(max,exits.size())));}
 public static class RunningAppProcessInfo {public int importance=125;}
 public static void getMyMemoryState(RunningAppProcessInfo info){}
 public boolean isBackgroundRestricted(){return false;}
}''',
'android/app/ApplicationExitInfo.java': '''package android.app;public class ApplicationExitInfo {
 public static final int REASON_UNKNOWN=0,REASON_EXIT_SELF=1,REASON_SIGNALED=2,REASON_LOW_MEMORY=3,REASON_CRASH=4,
 REASON_CRASH_NATIVE=5,REASON_ANR=6,REASON_INITIALIZATION_FAILURE=7,REASON_PERMISSION_CHANGE=8,REASON_EXCESSIVE_RESOURCE_USAGE=9,
 REASON_USER_REQUESTED=10,REASON_USER_STOPPED=11,REASON_DEPENDENCY_DIED=12,REASON_OTHER=13,REASON_FREEZER=14,
 REASON_PACKAGE_STATE_CHANGE=15,REASON_PACKAGE_UPDATED=16;
 public final int reason;public final long timestamp;public final String description;public String processName="app.topnote.personal";
 public ApplicationExitInfo(int r,long t,String d){reason=r;timestamp=t;description=d;}
 public int getReason(){return reason;}public long getTimestamp(){return timestamp;}public String getProcessName(){return processName;}
 public int getPid(){return 45678;}public int getStatus(){return 9;}public int getImportance(){return 125;}
 public String getDescription(){return description;}
}''',
'android/view/WindowManager.java': '''package android.view;import java.util.*;import android.graphics.Canvas;
public class WindowManager {
 public final Set<View> views=new HashSet<>();public int failures,adds,updates,updateFailures,removes;
 public boolean autoDraw=true;
 public void addView(View v,LayoutParams p){if(failures>0){failures--;throw new IllegalStateException("window transition");}views.add(v);v.attached=true;v.layout=p;v.invalidated=true;adds++;}
 public void updateViewLayout(View v,LayoutParams p){if(updateFailures>0){updateFailures--;throw new IllegalStateException();}if(!views.contains(v))throw new IllegalArgumentException();v.layout=p;updates++;v.invalidated=true;}
 public void removeView(View v){if(!views.remove(v))throw new IllegalArgumentException();v.attached=false;removes++;}
 public void detachAll(){for(View v:views)v.attached=false;views.clear();}
 public void renderFrames(){if(!autoDraw)return;for(View v:new ArrayList<>(views))if(v.invalidated&&v.isShown()&&v.getWindowVisibility()==View.VISIBLE){v.invalidated=false;v.draw(new Canvas());}}
 public static class LayoutParams {
 public static final int WRAP_CONTENT=-2,TYPE_APPLICATION_OVERLAY=2038,FLAG_NOT_FOCUSABLE=8,FLAG_NOT_TOUCHABLE=16;
 public int gravity,x,y;public float alpha;public LayoutParams(int w,int h,int type,int flags,int format){}
 public void setTitle(String s){}
 }
}''',
'android/widget/TextView.java': '''package android.widget; import android.content.*;import android.view.*;import android.graphics.*;
public class TextView extends View {
 public TextView(Context c){}public void setText(String s){}public void setTextSize(int s){}public void setTextColor(int c){}
 public void setTypeface(Typeface t,int s){}public void setSingleLine(boolean b){}public void setEllipsize(Object t){}
 public void setIncludeFontPadding(boolean b){}public void setPadding(int a,int b,int c,int d){}public void setMaxWidth(int w){}
 public void setBackground(Object b){}public void setShadowLayer(int r,int x,int y,int c){}
}''',
'android/widget/Toast.java': '''package android.widget;public class Toast {public static final int LENGTH_LONG=1;public static Toast makeText(android.content.Context c,String s,int d){return new Toast();}public void show(){}}''',
'app/topnote/personal/MainActivity.java': '''package app.topnote.personal;public class MainActivity {}''',
'app/topnote/personal/R.java': '''package app.topnote.personal;public class R {public static class drawable {public static final int ic_note=1;}}''',
'android/service/notification/StatusBarNotification.java': '''package android.service.notification;public class StatusBarNotification {
 private final int id;public StatusBarNotification(int i){id=i;}public int getId(){return id;}
}''',
'android/app/AlarmManager.java': '''package android.app;public class AlarmManager {
 public static final int ELAPSED_REALTIME=3,ELAPSED_REALTIME_WAKEUP=2;
 public int type,setCalls,cancelCalls;public long triggerAt;public PendingIntent operation;public boolean failSet;
 public void set(int t,long at,PendingIntent p){if(failSet)throw new SecurityException("alarm denied");type=t;triggerAt=at;operation=p;setCalls++;}
 public void cancel(PendingIntent p){cancelCalls++;if(operation==p)operation=null;}
}''',
'android/os/SystemClock.java': '''package android.os;public class SystemClock {
 public static long elapsed,uptime;
 public static void reset(){elapsed=1000000;uptime=1000000;}
 public static long elapsedRealtime(){return elapsed;}public static long uptimeMillis(){return uptime;}
 public static void advance(long ms){elapsed+=ms;uptime+=ms;}
 public static void sleepTime(long ms){elapsed+=ms;}
}''',
'android/os/Process.java': '''package android.os;public class Process {public static int myPid(){return 12345;}}''',
'android/graphics/Canvas.java': '''package android.graphics;public class Canvas {}''',
'android/graphics/Rect.java': '''package android.graphics;public class Rect {public int left,top,right,bottom;}''',
}
TEST = r'''package app.topnote.personal;
import android.app.*;import android.content.*;import android.os.*;import android.content.res.*;
public class PersistenceTest {
 static int checks;
 static void check(boolean value,String msg){checks++;if(!value)throw new AssertionError(msg);}
 static void enabled(boolean value){Context.prefs.edit().putBoolean("enabled",value).commit();}
 static boolean enabled(){return Context.prefs.getBoolean("enabled",false);}
 static void visible(int n){int visible=0;for(android.view.View v:Context.windows.views)if(v.getVisibility()==android.view.View.VISIBLE)visible++;
  check(visible==n,"visible windows expected "+n+", got "+visible);}
 static NoteService start(){NoteService s=new NoteService();s.onCreate();
  check(s.onStartCommand(null,0,1)==Service.START_STICKY,"enabled restart stays sticky");return s;}
 static void event(NoteService s,String event){Context.receiver.onReceive(s,new Intent(event));}
 static void reset(){Context.reset();NoteService.running=false;}
 static android.view.View onlyView(){check(Context.windows.views.size()==1,"one overlay window");return Context.windows.views.iterator().next();}
 static void recoveryTests(int sdk){
  reset();Context c=new Context();NoteRecoveryReceiver receiver=new NoteRecoveryReceiver();
  Intent checkAlarm=new Intent(NoteRecovery.CHECK);
  receiver.onReceive(c,checkAlarm);
  check(Context.startCalls==0&&Context.alarms.operation==null,"disabled note cannot be revived by delayed alarm");
  enabled(true);NoteRecovery.noteUserEnable(c);NoteRecovery.schedule(c);
  check(Context.alarms.type==AlarmManager.ELAPSED_REALTIME,"recovery alarm does not wake the phone");
  check(Context.alarms.triggerAt==SystemClock.elapsedRealtime()+600000L,"alarm uses elapsed time and a ten-minute request");
  check((Context.alarms.operation.flags&PendingIntent.FLAG_IMMUTABLE)!=0,"alarm pending intent is immutable");
  check(Context.alarms.operation.intent.target==NoteRecoveryReceiver.class,"alarm targets this app's receiver explicitly");
  int sets=Context.alarms.setCalls;
  receiver.onReceive(c,null);receiver.onReceive(c,new Intent("unrelated"));
  check(Context.alarms.setCalls==sets&&Context.startCalls==0,"unrelated broadcasts cannot trigger recovery");
  SystemClock.sleepTime(300000L);receiver.onReceive(c,checkAlarm);
  check(Context.startCalls==1&&NoteService.RECOVER.equals(Context.lastStart.getAction()),"delivered alarm requests idempotent service recovery");
  check(Context.alarms.triggerAt==SystemClock.elapsedRealtime()+600000L,"delivered alarm retains a future check after sleep");
  Context.denyStart=true;receiver.onReceive(c,checkAlarm);
  check(Context.startCalls==1&&Context.alarms.operation!=null&&enabled(),"denied background start keeps enabled choice and a future check");
  Context.denyStart=false;Context.alarms.failSet=true;NoteRecovery.schedule(c);
  check(enabled(),"alarm scheduling failure cannot disable the user's note");Context.alarms.failSet=false;
  Context.overlay=false;receiver.onReceive(c,checkAlarm);
  check(enabled()&&Context.startCalls==1&&Context.alarms.operation==null,"permission loss cancels recovery without forgetting the enabled choice");
  Context.overlay=true;NoteRecovery.schedule(c);enabled(false);receiver.onReceive(c,checkAlarm);
  check(Context.startCalls==1&&Context.alarms.operation==null,"Hide cancels a stale recovery alarm");
  reset();c=new Context();enabled(true);Context.prefs.edit().putLong("user_resume_wall",System.currentTimeMillis()+3600000L).commit();
  NoteRecovery.schedule(c);
  check(!NoteRecovery.mayRestore(c)&&enabled()&&Context.alarms.operation==null,"clock rollback defers automatic restore without discarding the enabled choice");
  if(sdk>=30){
   reset();c=new Context();enabled(true);
   long previousEnable=System.currentTimeMillis()-20000L;
   Context.prefs.edit().putLong("user_resume_wall",previousEnable).commit();NoteRecovery.schedule(c);
   ActivityManager.exits.add(new ApplicationExitInfo(ApplicationExitInfo.REASON_OTHER,previousEnable+1000L,"OEM"));
   ActivityManager.exits.add(new ApplicationExitInfo(ApplicationExitInfo.REASON_CRASH,previousEnable+1000L,"Crash"));
   ActivityManager.exits.add(new ApplicationExitInfo(ApplicationExitInfo.REASON_USER_REQUESTED,previousEnable-1000L,"old stop"));
   ApplicationExitInfo differentProcess=new ApplicationExitInfo(ApplicationExitInfo.REASON_USER_REQUESTED,previousEnable+1000L,"different process");
   differentProcess.processName="app.topnote.personal:other";ActivityManager.exits.add(differentProcess);
   check(NoteRecovery.mayRestore(c)&&enabled(),"old user stop, other process, crash and reason13 permit recovery");
   ActivityManager.exits.add(0,new ApplicationExitInfo(ApplicationExitInfo.REASON_USER_REQUESTED,previousEnable+1000L,"Task Manager Stop"));
   receiver.onReceive(c,checkAlarm);
   check(!enabled()&&Context.startCalls==0&&Context.alarms.operation==null,"new Android user stop cancels and disables automatic recovery");
   new RestoreReceiver().onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));
   check(Context.startCalls==0,"reboot cannot reverse an already detected user stop");
   NoteService stopped=new NoteService();stopped.onCreate();
   check(stopped.onStartCommand(null,0,1)==Service.START_NOT_STICKY,"stale sticky restart cannot reverse user stop");stopped.onDestroy();
   enabled(true);NoteRecovery.noteUserEnable(c);
   check(NoteRecovery.mayRestore(c),"explicit Show after a user stop permits future recovery");
   reset();c=new Context();enabled(true);
   ActivityManager.exits.add(new ApplicationExitInfo(ApplicationExitInfo.REASON_USER_REQUESTED,System.currentTimeMillis()-1000L,"legacy stop"));
   check(NoteRecovery.mayRestore(c)&&enabled()&&Context.prefs.getLong("user_resume_wall",0)>0,"upgrade adopts an already enabled legacy note once");
   long adopted=Context.prefs.getLong("user_resume_wall",0);NoteRecovery.mayRestore(c);
   check(Context.prefs.getLong("user_resume_wall",0)==adopted,"background recovery never refreshes user consent time");
   NoteRecovery.schedule(c);ActivityManager.failHistory=true;
   check(!NoteRecovery.mayRestore(c)&&enabled()&&Context.alarms.operation==null,"unavailable stop history defers recovery safely");
   int beforeStarts=Context.startCalls;receiver.onReceive(c,checkAlarm);
   check(Context.startCalls==beforeStarts,"failed history query cannot revive a possibly user-stopped process");
   NoteService explicit=new NoteService();explicit.onCreate();
   check(explicit.onStartCommand(new Intent(explicit,NoteService.class),0,1)==Service.START_STICKY,"explicit Show is still possible if exit history is unavailable");
   explicit.onStartCommand(new Intent(NoteService.STOP),0,2);explicit.onDestroy();ActivityManager.failHistory=false;
   for(String missingName:new String[]{null,""}){
    reset();c=new Context();enabled(true);long earlier=System.currentTimeMillis()-20000L;
    Context.prefs.edit().putLong("user_resume_wall",earlier).commit();NoteRecovery.schedule(c);
    ApplicationExitInfo stopWithoutName=new ApplicationExitInfo(ApplicationExitInfo.REASON_USER_REQUESTED,earlier+1000L,"Task Manager Stop");
    stopWithoutName.processName=missingName;ActivityManager.exits.add(stopWithoutName);
    check(!NoteRecovery.mayRestore(c)&&!enabled()&&Context.alarms.operation==null,"missing process name cannot bypass a newer Android user stop");
   }
  }
 }
 static void drawTests(){
  reset();enabled(true);NoteService s=start();Context.windows.renderFrames();
  android.view.View original=onlyView();int initialAdds=Context.windows.adds,initialUpdates=Context.windows.updates;
  for(int i=0;i<8;i++)Handler.next();
  check(Context.windows.adds==initialAdds&&onlyView()==original,"healthy periodic redraw preserves the same overlay");
  check(Context.windows.updates>initialUpdates,"a quiet awake service requests a fresh layout without needing a screen broadcast");
  check(s.onStartCommand(new Intent(s,NoteService.class).setAction(NoteService.RECOVER),0,2)==Service.START_STICKY,"OS recovery remains sticky");
  check(Context.windows.adds==initialAdds&&onlyView()==original,"OS recovery does not recreate a healthy window");
  ActivityManager.failHistory=true;
  check(NoteRecovery.mayRestore(s),"unavailable historical exits cannot stop an already running service");
  s.onStartCommand(new Intent(s,NoteService.class).setAction(NoteService.RECOVER),0,3);
  check(NoteService.running&&s.foreground&&Context.windows.adds==initialAdds,"live recovery preserves the service and window despite unavailable stop history");
  ActivityManager.failHistory=false;
  Context.windows.renderFrames();
  String report=NoteDiagnostics.report(s);
  check(report.contains("Last draw callback age: 0 s elapsed / 0 s awake-clock"),"diagnostics observe actual draw callback, not just a visible flag");
  check(report.contains("Text notification present: true"),"diagnostics inspect active notification");
  SystemClock.sleepTime(60000L);Handler.next();
  report=NoteDiagnostics.report(s);
  check(report.contains("65 s elapsed / 5 s awake-clock"),"sleep gap is distinguished from paused awake handler time");
  SystemClock.advance(40000L);Handler.next();
  check(NoteDiagnostics.report(s).contains("Recovery check gap:"),"long awake callback gaps are recorded");
  s.onDestroy();
  // A delayed real frame below the deadline must not trigger a rebuild.
  reset();enabled(true);Context.windows.autoDraw=false;s=start();initialAdds=Context.windows.adds;
  Handler.next();check(Context.windows.adds==initialAdds,"short draw delay is tolerated");
  Context.windows.autoDraw=true;Context.windows.renderFrames();
  for(int i=0;i<8;i++)Handler.next();
  check(Context.windows.adds==initialAdds,"successful delayed draw avoids replacement");s.onDestroy();
  // A locally visible attached view that never draws gets one bounded repair.
  reset();enabled(true);Context.windows.autoDraw=false;s=start();initialAdds=Context.windows.adds;
  Handler.next();Handler.next();
  check(Context.windows.adds==initialAdds+1,"missing draw triggers one replacement after the grace period");
  for(int i=0;i<30;i++)Handler.next();
  check(Context.windows.adds==initialAdds+1,"draw failure cannot cause an endless rebuild loop");
  s.onStartCommand(new Intent(s,NoteService.class).setAction(NoteService.RECOVER),0,2);
  for(int i=0;i<30;i++)Handler.next();
  check(Context.windows.adds==initialAdds+1,"periodic OS recovery cannot reset the one-rebuild safety budget");
  Context.power.interactive=false;event(s,Intent.ACTION_SCREEN_OFF);visible(0);
  SystemClock.sleepTime(3600000L);Context.power.interactive=true;event(s,Intent.ACTION_SCREEN_ON);
  initialAdds=Context.windows.adds;Handler.next();
  check(Context.windows.adds==initialAdds,"deep sleep is not counted against the awake draw deadline");
  Handler.next();check(Context.windows.adds==initialAdds+1,"new wake allows one fresh bounded repair");
  s.onStartCommand(new Intent(s,NoteService.class),0,3);initialAdds=Context.windows.adds;
  Handler.next();Handler.next();check(Context.windows.adds==initialAdds+1,"explicit Apply can reset the repair budget");
  s.onStartCommand(new Intent(NoteService.STOP),0,4);
  check(Context.alarms.operation==null&&Handler.queue.isEmpty(),"explicit Stop cancels both recovery mechanisms");s.onDestroy();
  // Reported system-hidden windows must not be repeatedly replaced.
  reset();enabled(true);s=start();Context.windows.autoDraw=false;onlyView().windowVisibility=android.view.View.INVISIBLE;
  initialAdds=Context.windows.adds;for(int i=0;i<30;i++)Handler.next();
  check(Context.windows.adds==initialAdds,"system-hidden window is not mistaken for a missing surface");
  check(NoteDiagnostics.report(s).contains("system visibility hidden"),"diagnostics distinguish system window suppression");
  onlyView().windowVisibility=android.view.View.VISIBLE;onlyView().shown=false;
  for(int i=0;i<30;i++)Handler.next();
  check(Context.windows.adds==initialAdds,"unshown overlay is not repeatedly recreated");s.onDestroy();
 }
 public static void main(String[] args){
  for(int sdk:new int[]{26,33,34,35}){
   Build.VERSION.SDK_INT=sdk; recoveryTests(sdk);drawTests();reset();enabled(true); NoteService s=start();visible(1);
   check(s.foreground,"foreground notification active");
   int initialAdds=Context.windows.adds;
   for(int cycle=0;cycle<20;cycle++){
    Context.power.interactive=false;Context.keyguard.locked=true;event(s,Intent.ACTION_SCREEN_OFF);visible(0);
    check(enabled() && NoteService.running,"screen off must not disable service");
    check(Context.windows.views.size()==1,"screen off must retain the window");
    Context.power.interactive=true;event(s,Intent.ACTION_SCREEN_ON);visible(0);
    event(s,Intent.ACTION_USER_PRESENT);visible(0); // Unlock broadcast arrives before Keyguard is ready.
    Handler.next();visible(0);
    Context.keyguard.locked=false;Handler.next();visible(1);
    int count=Context.windows.adds;event(s,Intent.ACTION_USER_PRESENT);Handler.next();visible(1);
    check(Context.windows.adds==count,"healthy overlay must not flicker/recreate");
    check(Handler.queue.size()==1,"exactly one recovery callback");
    check(Context.windows.adds==initialAdds,"sleep/wake must not recreate the window");
   }
   // Wake/unlock with broadcasts entirely missed.
   Context.power.interactive=false;Context.keyguard.locked=true;Handler.next();visible(0);
   Context.power.interactive=true;Context.keyguard.locked=false;Handler.next();visible(1);
   // A phone that refuses NEW background windows can still restore the old one.
   Context.windows.failures=100;Context.power.interactive=false;event(s,Intent.ACTION_SCREEN_OFF);
   Context.power.interactive=true;event(s,Intent.ACTION_SCREEN_ON);visible(1);
   check(Context.windows.failures==100,"wake must not request a new background window");Context.windows.failures=0;
   // Display callbacks recover visibility independently of broadcast delivery.
   Context.power.interactive=false;android.hardware.display.DisplayManager.listener.onDisplayChanged(0);visible(0);
   Context.power.interactive=true;android.hardware.display.DisplayManager.listener.onDisplayChanged(0);visible(1);
   check(Context.windows.updates>0,"wake refreshes window layout");
   // A transient WindowManager failure must never turn the setting off.
   Context.power.interactive=false;event(s,Intent.ACTION_SCREEN_OFF);
   Context.windows.detachAll();
   Context.power.interactive=true;Context.windows.failures=1;event(s,Intent.ACTION_SCREEN_ON);visible(0);
   check(enabled() && !s.stopped && s.foreground,"transient add failure preserves service and setting");
   Handler.next();visible(1);
   Context.windows.updateFailures=1;event(s,Intent.ACTION_USER_PRESENT);visible(0);
   check(enabled() && s.foreground,"layout refresh failure keeps enabled service");Handler.next();visible(1);
   Context.windows.detachAll();Handler.next();visible(1);
   s.onConfigurationChanged(new Configuration());visible(1);
   // Simulate OS destruction and sticky recreation, including while locked.
   s.onDestroy();visible(0);check(enabled() && Handler.queue.isEmpty(),"destroy cleans callbacks without disabling");
   check(android.hardware.display.DisplayManager.listener==null,"destroy unregisters display listener");
   Context.keyguard.locked=true;s=start();visible(0);Context.keyguard.locked=false;Handler.next();visible(1);
   // Permission loss pauses safely but doesn't discard the user's enabled choice.
   Context.overlay=false;Handler.next();visible(0);
   check(enabled() && s.stopped && !s.foreground && Handler.queue.isEmpty(),"permission loss pauses");s.onDestroy();
   Context.overlay=true;s=start();visible(1);
   // Stop and a queued/stale start must not resurrect the overlay.
   check(s.onStartCommand(new Intent(NoteService.STOP),0,2)==Service.START_NOT_STICKY,"explicit stop not sticky");visible(0);
   check(!enabled() && !NoteService.running && Handler.queue.isEmpty(),"stop clears choice and callbacks");
   check(s.onStartCommand(new Intent(s,NoteService.class),0,3)==Service.START_NOT_STICKY,"stale start respects stop");visible(0);s.onDestroy();
   // Hide in activity changes saved choice before stopService; pending refresh obeys it.
   enabled(true);s=start();enabled(false);Handler.next();visible(0);check(s.stopped,"Hide stops pending recovery");s.onDestroy();
   // Foreground promotion failure keeps the user's intended setting.
   enabled(true);s=new NoteService();s.onCreate();s.failForeground=true;
   check(s.onStartCommand(null,0,1)==Service.START_NOT_STICKY,"failed foreground launch is safely stopped");
   check(enabled() && s.stopped && Handler.queue.isEmpty(),"foreground failure preserves choice");
   check(Context.alarms.operation!=null&&Context.alarms.type==AlarmManager.ELAPSED_REALTIME,"foreground promotion failure retains a bounded non-waking recovery check");s.onDestroy();
   // A disabled or empty note cannot turn itself back on during a restart.
   reset();s=new NoteService();s.onCreate();
   check(s.onStartCommand(null,0,1)==Service.START_NOT_STICKY,"disabled null-intent restart stops");
   visible(0);s.onDestroy();
   enabled(true);Context.prefs.edit().putString("text","  ").commit();s=new NoteService();s.onCreate();
   check(s.onStartCommand(null,0,1)==Service.START_NOT_STICKY,"empty note stops without sticky restart");
   check(!enabled() && Handler.queue.isEmpty(),"empty note cannot loop");s.onDestroy();
   // Reboot/update resume enabled notes only; missing permission and denied starts are safe.
   reset();Context c=new Context();RestoreReceiver r=new RestoreReceiver();
   r.onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));check(Context.startCalls==0,"boot respects disabled note");
   enabled(true);r.onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));
   r.onReceive(c,new Intent(Intent.ACTION_MY_PACKAGE_REPLACED));check(Context.startCalls==2,"boot and update restore");
   r.onReceive(c,new Intent("unrelated"));r.onReceive(c,null);check(Context.startCalls==2,"unexpected broadcasts ignored");
   Context.overlay=false;r.onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));check(Context.startCalls==2,"boot respects permission");
   Context.overlay=true;Context.denyStart=true;r.onReceive(c,new Intent(Intent.ACTION_BOOT_COMPLETED));
   check(enabled() && Context.startCalls==2,"blocked autostart keeps choice without crashing");
   Context.prefs.edit().putString("text","PRIVATE_NOTE_NOT_FOR_REPORT").commit();
   for(int i=0;i<90;i++)NoteDiagnostics.record(c,"event "+i);
   String report=NoteDiagnostics.report(c);
   check(!report.contains("PRIVATE_NOTE_NOT_FOR_REPORT"),"report excludes note text");
   check(report.contains("event 89") && !report.contains("event 0\n"),"diagnostic history is bounded");
   check(Context.diagnostics.getString("events","").split("\n").length==64,"history keeps exactly its 64 newest records");
   NoteDiagnostics.record(c,"line one\nPRIVATE_NOTE_NOT_FOR_REPORT\tline two");
   check(Context.diagnostics.getString("events","").split("\n").length==64,"newlines cannot add unbounded event rows");
   check(!NoteDiagnostics.report(c).contains("PRIVATE_NOTE_NOT_FOR_REPORT"),"event history redacts note contents");
   if(sdk>=30){
    StringBuilder longDescription=new StringBuilder("OEM stop\nPRIVATE_NOTE_NOT_FOR_REPORT\t");
    for(int i=0;i<300;i++)longDescription.append('x');
    ActivityManager.exits.add(new ApplicationExitInfo(ApplicationExitInfo.REASON_OTHER,System.currentTimeMillis(),longDescription.toString()));
    report=NoteDiagnostics.report(c);
    check(report.contains("other (see description) (13)"),"reason 13 is other, not falsely diagnosed as crash");
    check(report.contains("PID: 45678; status: 9; importance: 125"),"exit evidence includes PID, status and importance");
    check(report.contains("[note redacted]")&&!report.contains("PRIVATE_NOTE_NOT_FOR_REPORT"),"OS exit description is redacted");
    for(String line:report.split("\n"))if(line.startsWith("  Description: "))
     check(line.length()<=215,"exit descriptions are bounded and single-line");
    ActivityManager.failHistory=true;
    check(NoteDiagnostics.report(c).contains("Process exit history unavailable"),"unavailable exit history is handled");
    ActivityManager.failHistory=false;
   }
  }
  System.out.println("PASS: "+checks+" assertions on actual service, restore/recovery receivers and diagnostics using fake Android APIs (26, 33, 34, 35 branches).");
  System.out.println("Physical device / emulator behavior remains untested.");
 }
}'''

with tempfile.TemporaryDirectory(prefix='topnote-test-') as folder:
    base = Path(folder)
    for name, source in STUBS.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    (base / 'app/topnote/personal/PersistenceTest.java').write_text(TEST)
    sources = list(base.rglob('*.java'))
    production = ROOT / 'app/src/main/java/app/topnote/personal'
    sources += [production / name for name in ('NoteService.java', 'NoteSettings.java', 'RestoreReceiver.java', 'NoteDiagnostics.java', 'NoteRecovery.java', 'NoteRecoveryReceiver.java')]
    output = base / 'classes'
    compiler = ['javac'] if shutil.which('javac') else ['java', '-jar', os.environ['JAVA_COMPILER_JAR'], '-proc:none', '-warn:none']
    subprocess.run(compiler + ['-source', '8', '-target', '8', '-d', str(output)] + [str(p) for p in sources], check=True)
    subprocess.run(['java', '-cp', str(output), 'app.topnote.personal.PersistenceTest'], check=True)
