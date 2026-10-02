package os.jarunix.shell;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Component;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.geom.Ellipse2D;
import java.awt.geom.RoundRectangle2D;
import javax.swing.Icon;

/** 用 Java2D 直接绘制的矢量图标，不依赖任何图片资源。 */
public final class Icons {
    private Icons() {}

    public interface Painter {
        void paint(Graphics2D g, int size);
    }

    private static Icon make(final int size, final Painter p) {
        return new Icon() {
            @Override public int getIconWidth()  { return size; }
            @Override public int getIconHeight() { return size; }
            @Override public void paintIcon(Component c, Graphics g, int x, int y) {
                Graphics2D g2 = (Graphics2D) g.create(x, y, size, size);
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                g2.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
                p.paint(g2, size);
                g2.dispose();
            }
        };
    }

    /** 按应用图标键取图标。 */
    public static Icon forKey(String key, int size) {
        if (key == null) return info(size);
        switch (key) {
            case "terminal":  return terminal(size);
            case "folder":    return folder(size);
            case "installer": return installer(size);
            case "java":      return java(size);
            default:          return info(size);
        }
    }

    public static Icon terminal(int n) {
        return make(n, (g, s) -> {
            g.setColor(new Color(0x0D, 0x11, 0x18));
            g.fill(new RoundRectangle2D.Float(1, 1, s - 2, s - 2, s / 4f, s / 4f));
            g.setColor(new Color(0x2A, 0x3A, 0x52));
            g.setStroke(new BasicStroke(1.2f));
            g.draw(new RoundRectangle2D.Float(1, 1, s - 2, s - 2, s / 4f, s / 4f));
            g.setColor(new Color(0x3D, 0xD6, 0x8C));
            g.setStroke(new BasicStroke(Math.max(1.6f, s / 12f), BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            int m = s / 4;
            g.drawLine(m, m, m + s / 5, s / 2);
            g.drawLine(m + s / 5, s / 2, m, s - m);
            g.drawLine(s / 2, s - m, s - m, s - m);
        });
    }

    public static Icon folder(int n) {
        return make(n, (g, s) -> {
            g.setColor(new Color(0xF2, 0xB4, 0x3B));
            g.fill(new RoundRectangle2D.Float(1, s * 0.22f, s - 2, s * 0.62f, s / 8f, s / 8f));
            g.setColor(new Color(0xD9, 0x9A, 0x22));
            g.fill(new RoundRectangle2D.Float(1, s * 0.14f, s * 0.45f, s * 0.22f, s / 10f, s / 10f));
        });
    }

    public static Icon installer(int n) {
        return make(n, (g, s) -> {
            g.setColor(new Color(0x2E, 0x9C, 0xF0));
            g.fill(new RoundRectangle2D.Float(1, 1, s - 2, s - 2, s / 5f, s / 5f));
            g.setColor(Color.WHITE);
            g.setStroke(new BasicStroke(Math.max(2f, s / 9f), BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            int m = s / 4;
            g.drawLine(m, s / 2, s - m, s / 2);
            g.drawLine(s / 2, m, s / 2, s - m);
        });
    }

    public static Icon info(int n) {
        return make(n, (g, s) -> {
            g.setColor(new Color(0x6C, 0x7A, 0x92));
            g.fill(new Ellipse2D.Float(1, 1, s - 2, s - 2));
            g.setColor(Color.WHITE);
            g.setStroke(new BasicStroke(Math.max(2f, s / 9f), BasicStroke.CAP_ROUND, BasicStroke.JOIN_ROUND));
            g.drawLine(s / 2, (int) (s * 0.30f), s / 2, (int) (s * 0.42f));
            g.drawLine(s / 2, (int) (s * 0.52f), s / 2, (int) (s * 0.76f));
        });
    }

    public static Icon java(int n) {
        return make(n, (g, s) -> {
            g.setColor(new Color(0xE7, 0x6F, 0x00));
            g.fill(new RoundRectangle2D.Float(1, 1, s - 2, s - 2, s / 5f, s / 5f));
            g.setColor(Color.WHITE);
            g.setFont(new java.awt.Font(java.awt.Font.SERIF, java.awt.Font.BOLD, (int) (s * 0.55f)));
            String t = "J";
            java.awt.FontMetrics fm = g.getFontMetrics();
            g.drawString(t, (s - fm.stringWidth(t)) / 2, (s + fm.getAscent() - fm.getDescent()) / 2);
        });
    }
}
