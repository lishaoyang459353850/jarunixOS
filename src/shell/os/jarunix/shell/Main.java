package os.jarunix.shell;

import javax.swing.SwingUtilities;
import javax.swing.UIManager;

/** jarunix-shell 入口。 */
public final class Main {
    private Main() {}

    public static void main(String[] args) {
        System.setProperty("awt.useSystemAAFontSettings", "on");
        System.setProperty("swing.aatext", "true");
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(new javax.swing.plaf.nimbus.NimbusLookAndFeel());
            } catch (Exception ignored) {
                // 回退到默认外观
            }
            new DesktopFrame().setVisible(true);
        });
    }
}
