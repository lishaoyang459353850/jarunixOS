package os.jarunix.installer;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.List;
import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.ButtonGroup;
import javax.swing.DefaultComboBoxModel;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JProgressBar;
import javax.swing.JRadioButton;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;

/** 向导页面的公共契约。 */
interface WizardPage {
    String title();
    default void onEnter() {}
    default boolean canAdvance() { return true; }
}

/** 页面通用样式。 */
final class Ui {
    private Ui() {}

    static final Color BG     = new Color(0x11, 0x18, 0x24);
    static final Color CARD   = new Color(0x1A, 0x24, 0x34);
    static final Color TEXT   = new Color(0xE8, 0xEF, 0xF7);
    static final Color DIM    = new Color(0x9A, 0xAC, 0xC4);
    static final Color ACCENT = new Color(0x2E, 0x9C, 0xF0);

    static JLabel title(String t) {
        JLabel l = new JLabel(t);
        l.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 20));
        l.setForeground(TEXT);
        l.setBorder(BorderFactory.createEmptyBorder(0, 0, 12, 0));
        return l;
    }

    static JLabel body(String t) {
        JLabel l = new JLabel("<html><body style='width:520px'>" + t + "</body></html>");
        l.setForeground(DIM);
        l.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 13));
        return l;
    }

    static JPanel page() {
        JPanel p = new JPanel();
        p.setBackground(BG);
        p.setLayout(new BoxLayout(p, BoxLayout.Y_AXIS));
        p.setBorder(BorderFactory.createEmptyBorder(28, 32, 24, 32));
        return p;
    }
}

/* ------------------------------------------------------------------ */

class WelcomePage extends JPanel implements WizardPage {
    WelcomePage() {
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("欢迎安装 jarunixOS"));
        box.add(Ui.body("这个向导会把 jarunixOS 安装到你的硬盘上。安装程序会为磁盘写入新的"
                + "分区表，<b>目标磁盘上的原有数据将被清空</b>，请提前备份。<br><br>"
                + "全程约需 5–15 分钟，取决于磁盘速度。"));
        box.add(Box.createVerticalStrut(18));
        box.add(Ui.body("提示：这是 Live 环境，你可以先试用桌面再决定是否安装。"));
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "欢迎"; }
}

/* ------------------------------------------------------------------ */

class EditionPage extends JPanel implements WizardPage {
    private final JRadioButton personal = new JRadioButton(
            "<html><b>个人版 Personal</b><br><span style='color:#9AACC4'>桌面外壳 + Java 运行时 + 安装器，体积最小</span></html>");
    private final JRadioButton pro = new JRadioButton(
            "<html><b>专业版 Professional</b><br><span style='color:#9AACC4'>个人版全部内容 + JDK、Git、GCC、Python、CMake 等开发工具链</span></html>");
    private final WizardModel model;

    EditionPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("选择版本"));
        box.add(Ui.body("两个版本共享同一套内核、图形栈与 Java 桌面，差别只在预装软件集合。"));
        box.add(Box.createVerticalStrut(16));

        ButtonGroup g = new ButtonGroup();
        g.add(personal);
        g.add(pro);
        for (JRadioButton b : new JRadioButton[]{personal, pro}) {
            b.setOpaque(false);
            b.setForeground(Ui.TEXT);
            b.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 13));
            b.setBorder(BorderFactory.createEmptyBorder(8, 4, 8, 4));
            box.add(b);
        }
        personal.setSelected(true);
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "版本"; }

    @Override public void onEnter() {
        personal.setSelected(!model.isProfessional());
        pro.setSelected(model.isProfessional());
    }

    @Override public boolean canAdvance() {
        model.edition = pro.isSelected() ? WizardModel.EDITION_PRO : WizardModel.EDITION_PERSONAL;
        return true;
    }
}

/* ------------------------------------------------------------------ */

class DiskPage extends JPanel implements WizardPage {
    private final WizardModel model;
    private final JList<String> list = new JList<>();
    private final JCheckBox confirm = new JCheckBox("我确认清空所选磁盘上的全部数据");

    DiskPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("选择安装磁盘"));
        box.add(Ui.body("请选择一块整盘。安装程序会在其上创建 GPT 分区表："
                + "一个 512 MB 的 EFI 系统分区，其余空间作为 ext4 根分区。"));
        box.add(Box.createVerticalStrut(14));

        list.setBackground(Ui.CARD);
        list.setForeground(Ui.TEXT);
        list.setSelectionBackground(Ui.ACCENT);
        list.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        JScrollPane sp = new JScrollPane(list);
        sp.setPreferredSize(new Dimension(520, 180));
        sp.setMaximumSize(new Dimension(Integer.MAX_VALUE, 180));
        box.add(sp);
        box.add(Box.createVerticalStrut(10));

        confirm.setOpaque(false);
        confirm.setForeground(Ui.TEXT);
        box.add(confirm);
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "磁盘"; }

    @Override public void onEnter() {
        List<String> disks = DiskUtil.listDisks();
        String[] rows = new String[disks.size()];
        for (int i = 0; i < disks.size(); i++) {
            String d = disks.get(i);
            rows[i] = String.format("%-16s %8s", d, DiskUtil.sizeOf(d));
        }
        list.setListData(rows);
        if (rows.length > 0) list.setSelectedIndex(0);
        confirm.setSelected(false);
    }

    @Override public boolean canAdvance() {
        int i = list.getSelectedIndex();
        if (i < 0) return false;
        if (!confirm.isSelected()) return false;
        List<String> disks = DiskUtil.listDisks();
        if (i >= disks.size()) return false;
        model.disk = disks.get(i);
        model.eraseDisk = true;
        return true;
    }
}

/* ------------------------------------------------------------------ */

class UserPage extends JPanel implements WizardPage {
    private final WizardModel model;
    private final JTextField hostname = new JTextField("jarunix", 18);
    private final JTextField username = new JTextField("jarunix", 18);
    private final JPasswordField pw1 = new JPasswordField(18);
    private final JPasswordField pw2 = new JPasswordField(18);
    private final JComboBox<String> tz = new JComboBox<>(new DefaultComboBoxModel<>(new String[]{
            "Asia/Shanghai", "Asia/Hong_Kong", "Asia/Taipei", "Asia/Tokyo",
            "Europe/London", "Europe/Berlin", "America/New_York", "America/Los_Angeles", "UTC"}));
    private final JComboBox<String> locale = new JComboBox<>(new DefaultComboBoxModel<>(new String[]{
            "zh_CN.UTF-8", "zh_TW.UTF-8", "en_US.UTF-8", "ja_JP.UTF-8"}));

    UserPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("账户与区域"));
        box.add(Ui.body("创建你的日常账户。root 账户会使用同一个密码。"));
        box.add(Box.createVerticalStrut(16));

        JPanel form = new JPanel(new GridBagLayout());
        form.setOpaque(false);
        form.setMaximumSize(new Dimension(Integer.MAX_VALUE, 260));
        GridBagConstraints c = new GridBagConstraints();
        c.insets = new Insets(6, 0, 6, 12);
        c.anchor = GridBagConstraints.WEST;

        int row = 0;
        add(form, c, row++, "计算机名", hostname);
        add(form, c, row++, "用户名", username);
        add(form, c, row++, "密码", pw1);
        add(form, c, row++, "确认密码", pw2);
        add(form, c, row++, "时区", tz);
        add(form, c, row, "语言", locale);
        box.add(form);
        add(box, BorderLayout.NORTH);
    }

    private void add(JPanel form, GridBagConstraints c, int row, String label, java.awt.Component field) {
        c.gridx = 0; c.gridy = row;
        JLabel l = new JLabel(label);
        l.setForeground(Ui.DIM);
        l.setPreferredSize(new Dimension(88, 26));
        form.add(l, c);
        c.gridx = 1;
        form.add(field, c);
    }

    @Override public String title() { return "账户"; }

    @Override public void onEnter() {
        hostname.setText(model.hostname);
        username.setText(model.username);
        tz.setSelectedItem(model.timezone);
        locale.setSelectedItem(model.locale);
    }

    @Override public boolean canAdvance() {
        String u = username.getText().trim();
        String h = hostname.getText().trim();
        String p1 = new String(pw1.getPassword());
        String p2 = new String(pw2.getPassword());
        if (h.isEmpty() || u.isEmpty()) return false;
        if (p1.isEmpty() || !p1.equals(p2)) return false;
        model.hostname = h;
        model.username = u;
        model.password = p1;
        model.timezone = String.valueOf(tz.getSelectedItem());
        model.locale = String.valueOf(locale.getSelectedItem());
        return true;
    }
}

/* ------------------------------------------------------------------ */

class ConfirmPage extends JPanel implements WizardPage {
    private final WizardModel model;
    private final JTextArea summary = new JTextArea(12, 52);

    ConfirmPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("确认并开始安装"));
        box.add(Ui.body("点击「开始安装」后立即开始写入磁盘。"));
        box.add(Box.createVerticalStrut(14));
        summary.setEditable(false);
        summary.setBackground(Ui.CARD);
        summary.setForeground(Ui.TEXT);
        summary.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 13));
        summary.setBorder(BorderFactory.createEmptyBorder(12, 14, 12, 14));
        box.add(summary);
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "确认"; }

    @Override public void onEnter() {
        summary.setText("""
                版本      : %s
                磁盘      : %s  (%s)
                计算机名  : %s
                用户名    : %s
                时区      : %s
                语言      : %s

                磁盘将被重新分区，原有数据不可恢复。
                """.formatted(
                model.isProfessional() ? "专业版 Professional" : "个人版 Personal",
                String.valueOf(model.disk), DiskUtil.sizeOf(String.valueOf(model.disk)),
                model.hostname, model.username, model.timezone, model.locale));
    }
}

/* ------------------------------------------------------------------ */

class ProgressPage extends JPanel implements WizardPage {
    private final WizardModel model;
    private final JTextArea log = new JTextArea(16, 62);
    private final JProgressBar bar = new JProgressBar();
    private InstallTask task;

    ProgressPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("正在安装"));
        bar.setIndeterminate(true);
        bar.setMaximumSize(new Dimension(Integer.MAX_VALUE, 18));
        box.add(bar);
        box.add(Box.createVerticalStrut(12));

        log.setEditable(false);
        log.setBackground(new Color(0x08, 0x0C, 0x12));
        log.setForeground(new Color(0x7B, 0xE3, 0xA8));
        log.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        JScrollPane sp = new JScrollPane(log);
        sp.setPreferredSize(new Dimension(560, 300));
        box.add(sp);
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "安装中"; }

    /** 由主窗口在进入本页时调用。 */
    public void startInstall() {
        if (task != null) return;
        task = new InstallTask(model) {
            @Override protected void process(List<String> chunks) {
                for (String s : chunks) {
                    log.append(s + "\n");
                }
                log.setCaretPosition(log.getDocument().getLength());
            }
        };
        task.addPropertyChangeListener(evt -> {
            if ("state".equals(evt.getPropertyName())
                    && evt.getNewValue() == javax.swing.SwingWorker.StateValue.DONE) {
                bar.setIndeterminate(false);
                bar.setValue(100);
            }
        });
        task.execute();
    }

    public boolean isRunning() {
        return task != null && !task.isDone();
    }
}

/* ------------------------------------------------------------------ */

class FinishPage extends JPanel implements WizardPage {
    private final WizardModel model;

    FinishPage(WizardModel model) {
        this.model = model;
        setLayout(new BorderLayout());
        setBackground(Ui.BG);
        JPanel box = Ui.page();
        box.add(Ui.title("安装完成"));
        box.add(Ui.body("jarunixOS 已写入磁盘。取出安装介质后重启即可进入新系统。<br><br>"
                + "首次启动会自动登录并拉起 Java 桌面外壳。"));
        box.add(Box.createVerticalStrut(20));

        JButton reboot = new JButton("立即重启");
        reboot.addActionListener(e -> {
            try {
                new ProcessBuilder("systemctl", "reboot").start();
            } catch (Exception ignored) {
                // 重启失败时保持界面
            }
        });
        JPanel row = new JPanel();
        row.setOpaque(false);
        row.setLayout(new BoxLayout(row, BoxLayout.X_AXIS));
        row.add(reboot);
        row.add(Box.createHorizontalGlue());
        box.add(row);
        add(box, BorderLayout.NORTH);
    }

    @Override public String title() { return "完成"; }

    @Override public void onEnter() {
        if (SwingUtilities.isEventDispatchThread()) {
            // 页面刷新即可
        }
    }
}
