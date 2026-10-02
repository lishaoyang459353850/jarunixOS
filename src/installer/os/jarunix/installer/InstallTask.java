package os.jarunix.installer;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import javax.swing.SwingWorker;

/**
 * 真正执行安装的后台任务。
 * 流程：停用交换 -> 分区 -> 格式化 -> 展开文件系统 -> 写入 fstab/主机名/用户
 *      -> 安装 GRUB（UEFI + BIOS）-> 卸载收尾。
 */
public class InstallTask extends SwingWorker<Void, String> {

    private static final String TARGET = "/target";

    private final WizardModel model;

    public InstallTask(WizardModel model) {
        this.model = model;
    }

    @Override
    protected Void doInBackground() throws Exception {
        try {
            step("停用交换分区", () ->
                    DiskUtil.run(List.of("swapoff", "-a"), this::publish));

            step("写入 GPT 分区表（ESP 512MB + 根分区）", () -> {
                Path table = Path.of("/tmp/jarunix.sfdisk");
                Files.writeString(table, "label: gpt\n,512M,U\n,,L\n",
                        StandardCharsets.UTF_8,
                        StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
                DiskUtil.runOrFail(List.of("sfdisk", "--wipe", "always", model.disk), this::publish);
                DiskUtil.runOrFail(List.of("bash", "-c",
                        "sfdisk " + model.disk + " < /tmp/jarunix.sfdisk"), this::publish);
                Thread.sleep(1500);
                DiskUtil.run(List.of("partprobe", model.disk), this::publish);
                Thread.sleep(1500);
            });

            String esp = partition(1);
            String root = partition(2);

            step("格式化 ESP 为 FAT32", () -> DiskUtil.runOrFail(
                    List.of("mkfs.vfat", "-F32", "-n", "JARUNIX-ESP", esp), this::publish));

            step("格式化根分区为 ext4", () -> DiskUtil.runOrFail(
                    List.of("mkfs.ext4", "-F", "-L", "jarunix-root", root), this::publish));

            step("建立目标目录并挂载根分区与 ESP", () -> {
                Files.createDirectories(Path.of(TARGET));
                DiskUtil.runOrFail(List.of("mount", root, TARGET), this::publish);
                Files.createDirectories(Path.of(TARGET + "/boot/efi"));
                DiskUtil.runOrFail(List.of("mount", esp, TARGET + "/boot/efi"), this::publish);
            });

            step("把 Live 文件系统展开到目标磁盘", () -> {
                Path squash = findSquashfs();
                if (squash != null) {
                    DiskUtil.runOrFail(List.of("unsquashfs", "-f", "-d", TARGET,
                            squash.toString()), this::publish);
                } else {
                    List<String> rsync = new ArrayList<>(List.of("rsync", "-aAXH", "--delete",
                            "--exclude=/proc", "--exclude=/sys", "--exclude=/dev",
                            "--exclude=/run", "--exclude=/tmp", "--exclude=/target",
                            "--exclude=/media", "--exclude=/lost+found", "/", TARGET + "/"));
                    DiskUtil.runOrFail(rsync, this::publish);
                }
            });

            step("写入 /etc/fstab", () -> {
                String fstab = "UUID=" + uuid(root) + "  /          ext4  defaults,noatime  0 1\n"
                        + "UUID=" + uuid(esp) + "  /boot/efi  vfat  umask=0077        0 2\n";
                Files.writeString(Path.of(TARGET + "/etc/fstab"), fstab, StandardCharsets.UTF_8);
            });

            step("配置主机名与时区", () -> {
                Files.writeString(Path.of(TARGET + "/etc/hostname"),
                        model.hostname + "\n", StandardCharsets.UTF_8);
                DiskUtil.run(List.of("ln", "-sf", "/usr/share/zoneinfo/" + model.timezone,
                        TARGET + "/etc/localtime"), this::publish);
            });

            step("创建用户并设置密码", () -> {
                String script = "set -e\n"
                        + "echo 'root:" + model.password + "' | chpasswd\n"
                        + "id -u " + model.username + " >/dev/null 2>&1 || "
                        + "useradd -m -s /bin/bash -G sudo " + model.username + "\n"
                        + "echo '" + model.username + ":" + model.password + "' | chpasswd\n"
                        + "echo '" + model.username + " ALL=(ALL) NOPASSWD: ALL' "
                        + "> /etc/sudoers.d/90-jarunix\n"
                        + "chmod 440 /etc/sudoers.d/90-jarunix\n";
                Files.writeString(Path.of("/tmp/jarunix-user.sh"), script, StandardCharsets.UTF_8);
                bindPseudoFs();
                DiskUtil.runOrFail(List.of("chroot", TARGET, "bash",
                        "/tmp/jarunix-user.sh"), this::publish);
            });

            step("安装 GRUB（UEFI 与 BIOS 双路径）", () -> {
                DiskUtil.run(List.of("chroot", TARGET, "grub-install",
                        "--target=x86_64-efi", "--efi-directory=/boot/efi",
                        "--bootloader-id=jarunix", "--recheck"), this::publish);
                DiskUtil.run(List.of("chroot", TARGET, "grub-install",
                        "--target=i386-pc", "--recheck", model.disk), this::publish);
                DiskUtil.run(List.of("chroot", TARGET, "update-grub"), this::publish);
            });

            step("写入版本标记", () -> Files.writeString(
                    Path.of(TARGET + "/etc/jarunix-edition"),
                    model.edition + "\n", StandardCharsets.UTF_8));

            step("收尾：卸载目标文件系统", () ->
                    DiskUtil.run(List.of("umount", "-R", TARGET), this::publish));

            publish("=== 安装完成 ===");
            return null;
        } catch (Exception e) {
            publish("!!! 安装失败：" + e.getMessage());
            try {
                DiskUtil.run(List.of("umount", "-R", TARGET), this::publish);
            } catch (Exception ignored) {
                // 尽力清理，忽略二次异常
            }
            throw e;
        }
    }

    private void bindPseudoFs() throws Exception {
        DiskUtil.run(List.of("mount", "--bind", "/dev", TARGET + "/dev"), this::publish);
        DiskUtil.run(List.of("mount", "--bind", "/proc", TARGET + "/proc"), this::publish);
        DiskUtil.run(List.of("mount", "--bind", "/sys", TARGET + "/sys"), this::publish);
    }

    private String partition(int index) {
        String d = model.disk;
        return d.matches(".*\\d$") ? d + "p" + index : d + index;
    }

    private String uuid(String dev) throws Exception {
        StringBuilder sb = new StringBuilder();
        DiskUtil.run(List.of("blkid", "-s", "UUID", "-o", "value", dev), sb::append);
        return sb.toString().trim();
    }

    private Path findSquashfs() {
        Path[] candidates = {
                Path.of("/run/live/medium/live/filesystem.squashfs"),
                Path.of("/run/live/rootfs/filesystem.squashfs"),
                Path.of("/lib/live/" + model.edition + "/filesystem.squashfs")
        };
        for (Path p : candidates) {
            if (Files.exists(p)) return p;
        }
        return null;
    }

    private void step(String name, ThrowingRunnable body) throws Exception {
        publish("");
        publish(">>> " + name);
        body.run();
    }

    private interface ThrowingRunnable {
        void run() throws Exception;
    }
}
