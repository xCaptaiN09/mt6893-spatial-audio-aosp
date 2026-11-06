import java.lang.reflect.InvocationTargetException;

/** Root app_process adapter to Android's Spatializer API; no raw binder numbers. */
public final class SpatialControl {
    static String quote(String s) {
        if (s == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (int i=0;i<s.length();i++) {
            char c=s.charAt(i);
            if (c=='\\' || c=='\"') b.append('\\').append(c);
            else if (c<32) b.append(String.format("\\u%04x", (int)c));
            else b.append(c);
        }
        return b.append('"').toString();
    }
    static Object invoke(Object object, String name) throws Exception {
        return object.getClass().getMethod(name).invoke(object);
    }
    public static void main(String[] args) {
        try {
            if (args.length!=1 || !("status".equals(args[0]) || "on".equals(args[0]) || "off".equals(args[0])))
                throw new IllegalArgumentException("Expected status, on or off");
            int uid=(Integer)Class.forName("android.os.Process").getMethod("myUid").invoke(null);
            if (uid!=0) throw new SecurityException("Root access is required");
            Class<?> looper=Class.forName("android.os.Looper");
            if (looper.getMethod("myLooper").invoke(null)==null)
                looper.getMethod("prepareMainLooper").invoke(null);
            Class<?> activity=Class.forName("android.app.ActivityThread");
            Object thread=activity.getMethod("systemMain").invoke(null);
            Object context=activity.getMethod("getSystemContext").invoke(thread);
            Object manager=Class.forName("android.content.Context").getMethod("getSystemService",String.class).invoke(context,"audio");
            Class<?> am=Class.forName("android.media.AudioManager");
            Object spatializer=am.getMethod("getSpatializer").invoke(manager);
            Class<?> type=Class.forName("android.media.Spatializer");
            if (!"status".equals(args[0])) {
                boolean wanted="on".equals(args[0]);
                type.getMethod("setEnabled",boolean.class).invoke(spatializer,wanted);
                boolean confirmed=false;
                for (int i=0;i<30;i++) {
                    if (((Boolean)type.getMethod("isEnabled").invoke(spatializer))==wanted) {confirmed=true;break;}
                    Thread.sleep(100);
                }
                if (!confirmed) throw new IllegalStateException("Android did not confirm the requested state");
            }
            boolean enabled=(Boolean)type.getMethod("isEnabled").invoke(spatializer);
            boolean available=(Boolean)type.getMethod("isAvailable").invoke(spatializer);
            int level=(Integer)type.getMethod("getImmersiveAudioLevel").invoke(spatializer);
            boolean tracker=false;
            try {tracker=(Boolean)type.getMethod("isHeadTrackerAvailable").invoke(spatializer);} catch (ReflectiveOperationException ignored) {}
            String device="No wired or USB headphones connected";
            Object[] devices=(Object[])am.getMethod("getDevices",int.class).invoke(manager,2);
            for (Object d:devices) {
                int dt=(Integer)invoke(d,"getType");
                if (dt==3 || dt==4 || dt==11 || dt==22) {
                    device=String.valueOf(invoke(d,"getProductName"));
                    if (dt==11 || dt==22) {device="USB · "+device;break;}
                    device="Wired · "+device;
                }
            }
            System.out.println("{\"enabled\":"+enabled+",\"available\":"+available+",\"level\":"+level+
                ",\"headTrackerAvailable\":"+tracker+",\"device\":"+quote(device)+"}");
            System.exit(0);
        } catch (Throwable error) {
            while (error instanceof InvocationTargetException && error.getCause()!=null) error=error.getCause();
            System.out.println("{\"error\":"+quote(error.getClass().getSimpleName()+": "+error.getMessage())+"}");
            System.exit(2);
        }
    }
}
