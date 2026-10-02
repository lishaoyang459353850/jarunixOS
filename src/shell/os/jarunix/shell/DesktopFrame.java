package os.jarunix.shell;

import java.awt.BorderLayout;
import java.awt.GraphicsEnvironment;
import java.awt.Rectangle;
import javax.swing.JFrame;

/** 桌面外壳主窗口：整屏无边框，中央为桌面，底部为任务栏。 */
public class DesktopFrame extends JFrame {

    public DesktopFrame() {
        super("jarunixOS Desktop");
        setUndecorated(true);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLayout(new BorderLayout());
        add(new WallpaperPanel(), BorderLayout.CENTER);
        add(new Taskbar(), BorderLayout.SOUTH);

        Rectangle bounds = GraphicsEnvironment.getLocalGraphicsEnvironment()
                .getDefaultScreenDevice().getDefaultConfiguration().getBounds();
        setBounds(bounds);
    }
}
