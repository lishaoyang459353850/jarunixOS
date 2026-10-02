package os.jarunix.shell;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.swing.BorderFactory;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;

/** 「关于本机」窗口。 */
public class About extends JFrame {

    public About() {
        super("关于 jarunixOS");
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setLayout(new BorderLayout());
        setPreferredSize(new Dimension(560, 380));

        JLabel head = new JLabel("jarunixOS", Icons.java(56), JLabel.LEFT);
        head.setFont(Theme.TITLE_FONT.deriveFont(22f));
        head.setBorder(BorderFactory.createEmptyBorder(16, 18, 8, 18));

        JTextArea info = new JTextArea(describe());
        info.setEditable(false);
        info.setFont(Theme.MONO_FONT);
        info.setBorder(BorderFactory.createEmptyBorder(0, 18, 18, 18));

        JPanel p = new JPanel(new BorderLayout());
        p.add(head, BorderLayout.NORTH);
        p.add(info, BorderLayout.CENTER);
        add(p, BorderLayout.CENTER);
        setLocationRelativeTo(null);
    }

    private String describe() {
        StringBuilder sb = new StringBuilder();
        sb.append("发行版      : jarunixOS\n");
        sb.append("版本        : ").append(readProp("jarunixOS.version", "1.0")).append('\n');
        sb.append("版本类型    : ").append(readProp("jarunixOS.edition", "unknown")).append('\n');
        sb.append("Java 运行时 : ").append(System.getProperty("java.version"))
          .append("  (").append(System.getProperty("java.vendor")).append(")\n");
        sb.append("Java 主目录 : ").append(System.getProperty("java.home")).append('\n');
        sb.append("操作系统    : ").append(System.getProperty("os.name")).append(' ')
          .append(System.getProperty("os.version")).append(' ')
          .append(System.getProperty("os.arch")).append('\n');
        sb.append("内核        : ").append(readFile(Path.of("/proc/version"))).append('\n');
        sb.append("处理器核心  : ").append(Runtime.getRuntime().availableProcessors()).append('\n');
        sb.append("内存上限    : ")
          .append(Runtime.getRuntime().maxMemory() / (1024 * 1024)).append(" MB\n");
        sb.append('\n').append("许可证：GNU GPL v3.0-or-later\n");
        return sb.toString();
    }

    private static String readProp(String key, String def) {
        String v = System.getProperty(key);
        return (v == null || v.isBlank()) ? def : v;
    }

    private static String readFile(Path p) {
        try {
            return Files.readString(p).trim();
        } catch (IOException e) {
            return "不可用";
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new About().setVisible(true));
    }
}
