package os.jarunix.installer;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** 磁盘枚举与外部命令执行。 */
public final class DiskUtil {
    private DiskUtil() {}

    /** 列出可作为安装目标的整块磁盘。 */
    public static List<String> listDisks() {
        List<String> out = new ArrayList<>();
        File[] devs = new File("/sys/block").listFiles();
        if (devs == null) return out;
        for (File d : devs) {
            String name = d.getName();
            if (name.startsWith("loop") || name.startsWith("ram")
                    || name.startsWith("dm-") || name.startsWith("sr")
                    || name.startsWith("zram") || name.startsWith("fd")) {
                continue;
            }
            if (name.startsWith("sd") || name.startsWith("vd") || name.startsWith("hd")
                    || name.startsWith("nvme") || name.startsWith("mmcblk")) {
                out.add("/dev/" + name);
            }
        }
        out.sort(String::compareTo);
        return out;
    }

    /** 读取块设备容量（人类可读）。 */
    public static String sizeOf(String dev) {
        try {
            Path p = Path.of("/sys/class/block/" + dev.replace("/dev/", "") + "/size");
            long sectors = Long.parseLong(Files.readString(p).trim());
            return (sectors * 512L) / (1000L * 1000L * 1000L) + " GB";
        } catch (Exception e) {
            return "未知";
        }
    }

    /** 执行命令，把输出逐行交给 logger，返回退出码。 */
    public static int run(List<String> cmd, Consumer<String> logger)
            throws IOException, InterruptedException {
        logger.accept("$ " + String.join(" ", cmd));
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        Process p = pb.start();
        try (BufferedReader r = new BufferedReader(
                new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) {
                logger.accept(line);
            }
        }
        int rc = p.waitFor();
        if (rc != 0) {
            logger.accept("[退出码 " + rc + "] " + String.join(" ", cmd));
        }
        return rc;
    }

    public static void runOrFail(List<String> cmd, Consumer<String> logger)
            throws IOException, InterruptedException, InstallException {
        if (run(cmd, logger) != 0) {
            throw new InstallException("命令执行失败：" + String.join(" ", cmd));
        }
    }

    /** 安装过程的可读异常。 */
    public static class InstallException extends Exception {
        public InstallException(String msg) { super(msg); }
    }
}
