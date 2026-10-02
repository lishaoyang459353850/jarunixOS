package os.jarunix.installer;

/** 安装向导收集到的全部选择。 */
public class WizardModel {
    public static final String EDITION_PERSONAL = "personal";
    public static final String EDITION_PRO      = "professional";

    public String edition  = EDITION_PERSONAL;
    public String disk     = null;
    public String hostname = "jarunix";
    public String username = "jarunix";
    public String password = "";
    public String timezone = "Asia/Shanghai";
    public String locale   = "zh_CN.UTF-8";
    public boolean eraseDisk = true;

    public boolean isProfessional() {
        return EDITION_PRO.equals(edition);
    }
}
