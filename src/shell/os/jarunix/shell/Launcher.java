package os.jarunix.shell;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** 应用注册表与进程启动。 */
public final class Launcher {
    private Launcher() {}

    private static final List<AppEntry> APPS = new ArrayList<>();

    static {
        APPS.add(new AppEntry("终端", "terminal", "terminal",
                "xterm", "-fa", "Monospace", "-fs", "11",
                "-bg", "#0D1118", "-fg", "#E6EDF3"));
        APPS.add(new AppEntry("文件", "files", "folder",
                "java", "-cp", "/opt/jarunix/jarunix-shell.jar",
                "os.jarunix.shell.FileBrowser"));
        APPS.add(new AppEntry("安装程序", "installer", "installer",
                "jarunix-install"));
        APPS.add(new AppEntry("关于本机", "about", "info",
                "java", "-cp", "/opt/jarunix/jarunix-shell.jar",
                "os.jarunix.shell.About"));
    }

    public static List<AppEntry> apps() { return APPS; }

    public static AppEntry byId(String id) {
        for (AppEntry a : APPS) {
            if (a.id().equals(id)) return a;
        }
        return null;
    }

    /** 启动应用，返回进程句柄；失败时抛出带可读原因的 IOException。 */
    public static Process launch(AppEntry app) throws IOException {
        ProcessBuilder pb = new ProcessBuilder(app.command());
        pb.redirectErrorStream(true);
        return pb.start();
    }
}
