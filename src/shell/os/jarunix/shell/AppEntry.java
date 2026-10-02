package os.jarunix.shell;

/** 一个可启动的应用项。 */
public final class AppEntry {
    private final String name;
    private final String id;
    private final String[] command;
    private final String iconKey;

    public AppEntry(String name, String id, String iconKey, String... command) {
        this.name = name;
        this.id = id;
        this.iconKey = iconKey;
        this.command = command;
    }

    public String name()      { return name; }
    public String id()        { return id; }
    public String iconKey()   { return iconKey; }
    public String[] command() { return command.clone(); }
}
