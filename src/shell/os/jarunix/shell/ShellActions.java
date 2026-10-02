package os.jarunix.shell;

import java.awt.Component;
import java.io.IOException;
import javax.swing.JOptionPane;

/** 外壳的公共动作：启动应用、电源操作、错误提示。 */
public final class ShellActions {
    private ShellActions() {}

    public static void launch(AppEntry app, Component parent) {
        try {
            Launcher.launch(app);
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(parent,
                    "无法启动「" + app.name() + "」：\n" + ex.getMessage(),
                    "jarunixOS", JOptionPane.WARNING_MESSAGE);
        }
    }

    public static void power(String action, Component parent) {
        int r = JOptionPane.showConfirmDialog(parent,
                switch (action) {
                    case "poweroff" -> "确定要关闭计算机吗？";
                    case "reboot"   -> "确定要重启吗？";
                    default         -> "确定要退出会话吗？";
                },
                "jarunixOS", JOptionPane.YES_NO_OPTION);
        if (r != JOptionPane.YES_OPTION) return;
        try {
            switch (action) {
                case "poweroff" -> new ProcessBuilder("sudo", "systemctl", "poweroff").start();
                case "reboot"   -> new ProcessBuilder("sudo", "systemctl", "reboot").start();
                default         -> System.exit(0);
            }
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(parent, "操作失败：" + ex.getMessage(),
                    "jarunixOS", JOptionPane.ERROR_MESSAGE);
        }
    }
}
