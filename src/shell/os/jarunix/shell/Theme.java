package os.jarunix.shell;

import java.awt.Color;
import java.awt.Font;

/** 全局配色与字体。 */
public final class Theme {
    private Theme() {}

    public static final Color BG_TOP     = new Color(0x1B, 0x2A, 0x41);
    public static final Color BG_BOTTOM  = new Color(0x08, 0x10, 0x1C);
    public static final Color ACCENT     = new Color(0x2E, 0x9C, 0xF0);
    public static final Color TASKBAR_BG = new Color(0x12, 0x1A, 0x28);
    public static final Color BORDER     = new Color(0x2A, 0x3A, 0x52);
    public static final Color TEXT       = new Color(0xEC, 0xF2, 0xFA);
    public static final Color TEXT_DIM   = new Color(0x9F, 0xB0, 0xC6);

    public static final Font UI_FONT    = new Font(Font.SANS_SERIF, Font.PLAIN, 13);
    public static final Font TITLE_FONT = new Font(Font.SANS_SERIF, Font.BOLD, 15);
    public static final Font MONO_FONT  = new Font(Font.MONOSPACED, Font.PLAIN, 13);
}
