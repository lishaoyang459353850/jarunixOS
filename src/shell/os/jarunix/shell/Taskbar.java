package os.jarunix.shell;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.text.SimpleDateFormat;
import java.util.Date;
import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JSeparator;
import javax.swing.SwingConstants;
import javax.swing.Timer;

/** 底部任务栏：开始菜单、任务区、时钟。 */
public class Taskbar extends JPanel {

    private final JLabel clock = new JLabel();
    private final JPopupMenu menu = new JPopupMenu();
    private final SimpleDateFormat fmt = new SimpleDateFormat("yyyy-MM-dd  HH:mm:ss");

    public Taskbar() {
        super(new BorderLayout());
        setPreferredSize(new Dimension(0, 38));
        setBackground(Theme.TASKBAR_BG);
        setBorder(BorderFactory.createMatteBorder(1, 0, 0, 0, Theme.BORDER));

        buildMenu();

        JButton start = new JButton("jarunix", Icons.java(18));
        start.setFocusPainted(false);
        start.setFont(Theme.TITLE_FONT);
        start.setForeground(Theme.TEXT);
        start.setBackground(Theme.TASKBAR_BG);
        start.setBorder(BorderFactory.createEmptyBorder(4, 12, 4, 14));
        start.addActionListener(e -> menu.show(start, 0, -menu.getPreferredSize().height));

        JPanel left = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 3));
        left.setOpaque(false);
        left.add(start);
        for (AppEntry app : Launcher.apps()) {
            JButton b = new JButton(app.name(), Icons.forKey(app.iconKey(), 18));
            b.setFocusPainted(false);
            b.setFont(Theme.UI_FONT);
            b.setForeground(Theme.TEXT_DIM);
            b.setBackground(Theme.TASKBAR_BG);
            b.setBorder(BorderFactory.createEmptyBorder(4, 10, 4, 10));
            b.setToolTipText(app.name());
            b.addActionListener(e -> ShellActions.launch(app, this));
            left.add(b);
        }

        clock.setFont(Theme.MONO_FONT);
        clock.setForeground(Theme.TEXT);
        clock.setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 14));
        clock.setHorizontalAlignment(SwingConstants.RIGHT);
        tick();
        new Timer(1000, e -> tick()).start();

        add(left, BorderLayout.WEST);
        add(Box.createHorizontalGlue(), BorderLayout.CENTER);
        add(clock, BorderLayout.EAST);
    }

    private void tick() {
        clock.setText(fmt.format(new Date()));
    }

    private void buildMenu() {
        for (AppEntry app : Launcher.apps()) {
            JButton item = new JButton(app.name(), Icons.forKey(app.iconKey(), 20));
            item.setHorizontalAlignment(SwingConstants.LEFT);
            item.addActionListener(e -> {
                menu.setVisible(false);
                ShellActions.launch(app, this);
            });
            menu.add(item);
        }
        menu.add(new JSeparator());
        JButton reboot = new JButton("重启");
        reboot.addActionListener(e -> { menu.setVisible(false); ShellActions.power("reboot", this); });
        JButton poweroff = new JButton("关机");
        poweroff.addActionListener(e -> { menu.setVisible(false); ShellActions.power("poweroff", this); });
        JButton logout = new JButton("退出会话");
        logout.addActionListener(e -> { menu.setVisible(false); ShellActions.power("logout", this); });
        menu.add(reboot);
        menu.add(poweroff);
        menu.add(logout);
    }
}
