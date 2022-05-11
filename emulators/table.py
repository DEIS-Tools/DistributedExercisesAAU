import tkinter as TK

class table(TK.Frame):
    rows:list[TK.Frame]
    labels:list[list[TK.Label]]
    master:TK.Toplevel
    column_width:list[int]

    def __init__(self, master = None, content:list[list]=[], width=2, height=2, title="", icon="", scrollable = "None"):
        if not len(content) > 0 or not len(content[0]) > 0:
            print("failed to make table: bad list")
            return
        
        if master == None:
            master = TK.Toplevel()
        self.master = master
        TK.Frame.__init__(self, self.master)
        if type(self.master) is TK.Toplevel:
            self.master.resizable(False,False)
            self.master.title(title)
            if not icon == "":
                try:
                    self.master.iconbitmap(icon)
                except:
                    print("failed to set window icon")
        rows = len(content)
        cols = len(content[0])
        self.column_width = [width for _ in range(cols)]
        for j in range(cols):
            for i in range(rows):
                if type(content[i][j]) == str:
                    if len(content[i][j]) > self.column_width[j]:
                        self.column_width[j] = len(content[i][j])
                elif width > self.column_width[j]:
                    self.column_width[j] = width
                    
        if scrollable == "None":
            container = self
        elif scrollable == "x":
            if len(content) > 10:
                mod = 10
            else:
                mod = len(content)
            __container = ScrollableFrame_X(self, width=sum(self.column_width), height=height*mod*20)
            container = __container.scrollable_frame
            __container.pack(side=TK.LEFT)
        elif scrollable == "y":
            if len(content) > 10:
                mod = 10
            else:
                mod = len(content)
            __container = ScrollableFrame_Y(self, width=sum(self.column_width)*7.5, height=height*mod*20)
            container = __container.scrollable_frame
            __container.pack(side=TK.LEFT)
        self.rows = [TK.LabelFrame(container) for i in range(rows)]
        [self.rows[i].pack(side=TK.TOP) for i in range(len(self.rows))]
        for j in range(cols):
            for i in range(rows):
                TK.Label(self.rows[i], text=content[i][j], width=self.column_width[j], height=height).pack(side=TK.LEFT)
class ScrollableFrame_Y(TK.Frame):
    ###source: https://blog.teclado.com/tkinter-scrollable-frames/
    def __init__(self, container, width=300, height=300, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = TK.Canvas(self)
        scrollbar = TK.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = TK.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set, width=width, height=height)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class ScrollableFrame_X(TK.Frame):
    ###source: https://blog.teclado.com/tkinter-scrollable-frames/
    def __init__(self, container, width=300, height=300, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = TK.Canvas(self)
        scrollbar = TK.Scrollbar(self, orient="horizontal", command=canvas.xview)
        self.scrollable_frame = TK.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(xscrollcommand=scrollbar.set, width=width, height=height)

        canvas.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="bottom", fill="x")