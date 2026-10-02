package os.jarunix.installer;

import java.awt.BorderLayout;
import java.awt.CardLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.List;
import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;

/** jarunixOS 图形化安装程序主窗口。 */
public class InstallerMain extends JFrame {

    private final WizardModel model = new WizardModel();
    private final CardLayout cards = new CardLayout();
    private final JPanel deck = new JPanel(cards);
    private final List<WizardPage> pages = new ArrayList<>();
    private final JLabel stepLabel = new JLabel();
    private final JButton back = new JButton("上一步");
    private final JButton next = new JButton("下一步");

    private int index = 0;

    public InstallerMain() {
        super("安装 jarunixOS");
        setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
        setPreferredSize(new Dimension(700, 560));
        setLayout(new BorderLayout());
        getContentPane().setBackground(Ui.BG);

        add(header(), BorderLayout.NORTH);

        deck.setBackground(Ui.BG);
        pages.add(new WelcomePage());
        pages.add(new EditionPage(model));
        pages.add(new DiskPage(model));
        pages.add(new UserPage(model));
        pages.add(new ConfirmPage(model));
        pages.add(new ProgressPage(model));
        pages.add(new FinishPage(model));
        for (int i = 0; i < pages.size(); i++) {
            deck.add((java.awt.Component) pages.get(i), String.valueOf(i));
        }
        add(deck, BorderLayout.CENTER);
        add(footer(), BorderLayout.SOUTH);

        addWindowListener(new WindowAdapter() {
            @Override public void windowClosing(WindowEvent e) {
                WizardPage p = pages.get(index);
                if (p instanceof ProgressPage pg && pg.isRunning()) {
                    JOptionPane.showMessageDialog(InstallerMain.this,
                            "安装正在进行中，请不要关闭窗口。",
                            "jarunixOS", JOptionPane.WARNING_MESSAGE);
                    return;
                }
                int r = JOptionPane.showConfirmDialog(InstallerMain.this,
                        "确定要退出安装程序吗？", "jarunixOS", JOptionPane.YES_NO_OPTION);
                if (r == JOptionPane.YES_OPTION) dispose();
            }
        });

        show(0);
        pack();
        setLocationRelativeTo(null);
    }

    private JPanel header() {
        JPanel h = new JPanel(new BorderLayout());
        h.setBackground(new Color(0x0B, 0x12, 0x1C));
        h.setBorder(BorderFactory.createEmptyBorder(14, 20, 14, 20));

        JLabel brand = new JLabel("jarunixOS");
        brand.setFont(new Font(Font.SANS_SERIF, Font.BOLD, 18));
        brand.setForeground(Ui.TEXT);
        h.add(brand, BorderLayout.WEST);

        stepLabel.setForeground(Ui.DIM);
        stepLabel.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, 12));
        h.add(stepLabel, BorderLayout.EAST);
        return h;
    }

    private JPanel footer() {
        JPanel f = new JPanel();
        f.setBackground(new Color(0x0B, 0x12, 0x1C));
        f.setLayout(new BoxLayout(f, BoxLayout.X_AXIS));
        f.setBorder(BorderFactory.createEmptyBorder(12, 20, 14, 20));

        back.addActionListener(e -> {
            if (index > 0) show(index - 1);
        });
        next.addActionListener(e -> onNext());

        f.add(back);
        f.add(Box.createHorizontalGlue());
        f.add(next);
        return f;
    }

    private void onNext() {
        WizardPage p = pages.get(index);
        if (p instanceof ProgressPage pg) {
            if (pg.isRunning()) {
                JOptionPane.showMessageDialog(this, "安装尚未结束，请稍候。",
                        "jarunixOS", JOptionPane.INFORMATION_MESSAGE);
                return;
            }
            show(index + 1);
            return;
        }
        if (p instanceof FinishPage) {
            dispose();
            return;
        }
        if (!p.canAdvance()) {
            JOptionPane.showMessageDialog(this,
                    "请先完成本页的必填项（磁盘需勾选确认）。",
                    "jarunixOS", JOptionPane.WARNING_MESSAGE);
            return;
        }
        show(index + 1);
    }

    private void show(int i) {
        index = Math.max(0, Math.min(i, pages.size() - 1));
        cards.show(deck, String.valueOf(index));
        WizardPage p = pages.get(index);
        p.onEnter();
        stepLabel.setText((index + 1) + " / " + pages.size() + "  ·  " + p.title());
        back.setEnabled(index > 0 && !(p instanceof ProgressPage) && !(p instanceof FinishPage));
        next.setText(index == pages.size() - 1 ? "结束" : "下一步");
        if (p instanceof ProgressPage pg) {
            next.setEnabled(true);
            pg.startInstall();
        }
        if (p instanceof FinishPage) {
            next.setText("结束");
        }
    }

    public static void main(String[] args) {
        if (!"0".equals(System.getProperty("user.name")) && System.getProperty("os.name").contains("Linux")) {
            // 仅提示，不强制：真实判定交给后端命令的返回值
            System.err.println("[jarunix-installer] 提示：安装程序需要 root 权限才能写入磁盘。");
        }
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(new javax.swing.plaf.nimbus.NimbusLookAndFeel());
            } catch (Exception ignored) {
                // 回退到默认外观
            }
            new InstallerMain().setVisible(true);
        });
    }
}
