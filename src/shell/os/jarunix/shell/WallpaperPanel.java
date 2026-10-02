package os.jarunix.shell;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.GradientPaint;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JPanel;

/** 桌面背景 + 左侧图标栏，整块由 Java2D 绘制。 */
public class WallpaperPanel extends JPanel {

    public WallpaperPanel() {
        setOpaque(true);
        setLayout(new BorderLayout());

        JPanel column = new JPanel();
        column.setOpaque(false);
        column.setLayout(new BoxLayout(column, BoxLayout.Y_AXIS));
        column.setBorder(BorderFactory.createEmptyBorder(18, 18, 18, 18));
        for (AppEntry app : Launcher.apps()) {
            column.add(new DesktopIcon(app));
            column.add(Box.createVerticalStrut(6));
        }
        add(column, BorderLayout.WEST);
    }

    @Override protected void paintComponent(Graphics g) {
        Graphics2D g2 = (Graphics2D) g.create();
        g2.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setPaint(new GradientPaint(0, 0, Theme.BG_TOP, 0, Math.max(1, getHeight()), Theme.BG_BOTTOM));
        g2.fillRect(0, 0, getWidth(), getHeight());

        g2.setColor(new Color(255, 255, 255, 16));
        g2.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 64));
        FontMetrics fm = g2.getFontMetrics();
        String watermark = "jarunixOS";
        g2.drawString(watermark, Math.max(20, getWidth() - fm.stringWidth(watermark) - 48),
                Math.max(80, getHeight() - 48));
        g2.dispose();
    }
}
