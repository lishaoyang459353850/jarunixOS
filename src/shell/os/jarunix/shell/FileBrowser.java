package os.jarunix.shell;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.io.File;
import java.util.Arrays;
import java.util.Comparator;
import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

/** 极简 Java 文件浏览器（可独立启动）。 */
public class FileBrowser extends JFrame {

    private final DefaultListModel<String> model = new DefaultListModel<>();
    private final JList<String> list = new JList<>(model);
    private final JTextField path = new JTextField();
    private File dir;

    public FileBrowser() {
        this(new File(System.getProperty("user.home", "/")));
    }

    public FileBrowser(File start) {
        super("文件 — jarunixOS");
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setPreferredSize(new Dimension(720, 480));
        setLayout(new BorderLayout());

        JButton up = new JButton("上一级");
        up.addActionListener(e -> open(dir != null && dir.getParentFile() != null
                ? dir.getParentFile() : dir));
        JButton home = new JButton("主目录");
        home.addActionListener(e -> open(new File(System.getProperty("user.home", "/"))));

        path.setEditable(false);
        JPanel top = new JPanel(new BorderLayout(6, 0));
        JPanel btns = new JPanel();
        btns.add(up);
        btns.add(home);
        top.add(btns, BorderLayout.WEST);
        top.add(path, BorderLayout.CENTER);
        add(top, BorderLayout.NORTH);

        list.setFont(Theme.MONO_FONT);
        list.addMouseListener(new MouseAdapter() {
            @Override public void mouseClicked(MouseEvent e) {
                if (e.getClickCount() >= 2) {
                    String sel = list.getSelectedValue();
                    if (sel == null || sel.startsWith("..")) return;
                    File f = new File(dir, sel);
                    if (f.isDirectory()) open(f);
                }
            }
        });
        add(new JScrollPane(list), BorderLayout.CENTER);

        open(start);
        setLocationRelativeTo(null);
    }

    private void open(File target) {
        if (target == null || !target.isDirectory()) return;
        dir = target;
        path.setText(dir.getAbsolutePath());
        model.clear();
        File[] children = dir.listFiles();
        if (children != null) {
            Arrays.sort(children, Comparator
                    .comparing((File f) -> !f.isDirectory())
                    .thenComparing(f -> f.getName().toLowerCase()));
            for (File f : children) {
                model.addElement(f.getName() + (f.isDirectory() ? "/" : ""));
            }
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new FileBrowser().setVisible(true));
    }
}
