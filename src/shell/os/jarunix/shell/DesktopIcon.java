package os.jarunix.shell;

import java.awt.Color;
import java.awt.Cursor;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import javax.swing.Icon;
import javax.swing.JComponent;

/** 桌面上的一个应用图标（Java2D 自绘，无外部资源）。 */
public class DesktopIcon extends JComponent {
    private static final int W = 84;
    private static final int H = 84;

    private final AppEntry app;
    private boolean hover;

    public DesktopIcon(final AppEntry app) {
        this.app = app;
        setPreferredSize(new Dimension(W, H));
        setMinimumSize(new Dimension(W, H));
        setMaximumSize(new Dimension(W, H));
        setToolTipText(app.name());
        setCursor(Cursor.getPredefinedCursor(Cursor.HAND_CURSOR));
        addMouseListener(new MouseAdapter() {
            @Override public void mouseEntered(MouseEvent e) { hover = true;  repaint(); }
            @Override public void mouseExited (MouseEvent e) { hover = false; repaint(); }
            @Override public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() >= 1) ShellActions.launch(app, DesktopIcon.this);
            }
        });
    }

    @Override protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        if (hover) {
            g2.setColor(new Color(255, 255, 255, 38));
            g2.fillRoundRect(0, 0, getWidth(), getHeight(), 12, 12);
            g2.setColor(new Color(255, 255, 255, 60));
            g2.drawRoundRect(0, 0, getWidth() - 1, getHeight() - 1, 12, 12);
        }
        Icon ic = Icons.forKey(app.iconKey(), 46);
        ic.paintIcon(this, g2, (getWidth() - 46) / 2, 8);
        g2.setFont(Theme.UI_FONT.deriveFont(Font.PLAIN, 12f));
        g2.setColor(Theme.TEXT);
        String t = app.name();
        int tw = g2.getFontMetrics().stringWidth(t);
        g2.drawString(t, (getWidth() - tw) / 2, 70);
        g2.dispose();
    }
}
