from PIL import Image
import numpy as np
import json 
from sklearn.linear_model import LinearRegression
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinter import simpledialog

def trim_image(img:np.ndarray):
    img = img
    # find top
    r,c,_ = img.shape

    max_r = (255 + 255 + 255 + 255)*c
    

    top_row = -1
    bottom_row = r-1
    for i in range(r):
        if top_row == -1 and np.sum(img[i,:],axis=None) != max_r:
            top_row = i
        elif top_row != -1 and np.sum(img[i,:],axis=None) == max_r:
            bottom_row = i-1
            break


    max_c = (255 + 255 + 255 + 255)*r
    top_col = -1
    bottom_col = r-1
    for i in range(c):
        if top_col == -1 and np.sum(img[:,i],axis=None) != max_c:
            top_col = i
        elif top_col != -1 and np.sum(img[:,i],axis=None) == max_c:
            bottom_col = i-1
            break
    
    img = img[top_row:bottom_row+1,top_col:bottom_col+1,:]
    return img
        
def scale_map_calculate(pos,map_dim):
    # {v["x"]} {v["y"]} <| {v["lat"]} {v["lon"]}

    x_train = []
    y_train = []
    for p in pos:
        x_train.append([p["x"],p["y"]])
        y_train.append([p["lat"],p["lon"]])
    
    x_train,y_train = np.array(x_train),np.array(y_train)

    cord_to_geo = LinearRegression().fit(x_train,y_train)
    
    dim = cord_to_geo.predict([[0,map_dim[1]],[map_dim[0],0]])

    get_pos = lambda x,y : cord_to_geo.predict([[x,y]])[0].tolist()

    return dim,get_pos


class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Precision-Geo-Building-Mapping-Tool")

        self.pos_list = []
        

        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.scroll_x = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.scroll_y = tk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.config(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.scroll_x.config(command=self.canvas.xview)
        self.scroll_y.config(command=self.canvas.yview)

        self.tool_widgets = []

        self.load_button = tk.Button(self.root, text="New Level", command=self.load_image)
        self.load_button.pack(side="right")

        self.mark_tool_button = tk.Button(self.root, text="Mark", command=lambda : self.use_tool("Mark"))
        self.mark_tool_button.pack(side="left")
        self.tool_widgets.append(self.mark_tool_button)

        self.pan_tool_button = tk.Button(self.root, text="Pan", command=lambda : self.use_tool("Pan"))
        self.pan_tool_button.pack(side="left")
        self.tool_widgets.append(self.pan_tool_button)

        self.line_tool_button = tk.Button(self.root, text="Line", command=lambda : self.use_tool("Line"))
        self.line_tool_button.pack(side="left")
        self.tool_widgets.append(self.line_tool_button)

        self.delete_tool_button = tk.Button(self.root, text="Del", command=lambda : self.use_tool("Del"))
        self.delete_tool_button.pack(side="left")
        self.tool_widgets.append(self.delete_tool_button)

        self.pos_tool_button = tk.Button(self.root, text="Pos", command=lambda : self.use_tool("Pos"))
        self.pos_tool_button.pack(side="left")
        self.tool_widgets.append(self.pos_tool_button)

        self.save_tool_button = tk.Button(self.root, text="Save", command = self.save_file)
        self.save_tool_button.pack(side="right")

        self.load_tool_button = tk.Button(self.root, text="Load", command = self.load_file)
        self.load_tool_button.pack(side="right")

        self.load_tool_button = tk.Button(self.root, text="CL", command = self.change_level)
        self.load_tool_button.pack(side="right")

        # print(self.canvas.winfo_height())

        self.floating_button = tk.Button(self.root, text="I", command = self.open_another_window)
        self.floating_button.place(relx = 0.90, rely = 0.02, width=30)

        self.image = None
        self.img_width = 0
        self.img_height = 0
        self.prev_x = None
        self.prev_y = None

        self.cords = []

        self.level_data = []

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        self.tool = None
        self.use_tool("Pan")

        self.left_top = {"x":0,"y":0}
        self.frame = None

        self.get_pos = None
        
        self.level_index = 0
        self.current_level = 0

    def save_file(self):
        self.save_level()
        #print(self.level_data)
        project_name = simpledialog.askstring("Input", "Enter Project_name :")

        with open(f"project/{project_name}.json", "w") as outfile: 
            json.dump(self.level_data, outfile)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON file", "*.json")])
        with open(file_path, "r") as f: 
            data = json.load(f)
            self.level_data = data
            self.change_level()

    def change_level(self):
        self.level_index += 1
        if self.level_index == len(self.level_data):
            self.level_index = 0
        self.current_level = self.level_data[self.level_index]["level"]
        self.file_path = self.level_data[self.level_index]["filepath"]
        #self.set_image(self.file_path)
        self.re_rendered()

        self.cords = self.level_data[self.level_index]["mark"]
        self.pos_list = self.level_data[self.level_index]["pos_cord"]

    def save_level(self):
        # {"level":level,"filepath":file_path,"mark":[],"pos_cord":[]}

        self.level_data[self.level_index]["mark"] = self.cords
        self.level_data[self.level_index]["pos_cord"] = self.pos_list

        if len(self.pos_list) >= 2:
            res,get_pos = scale_map_calculate(self.pos_list,[self.img_width,self.img_height])
            dl,ur = res[0].tolist(),res[1].tolist()
            self.level_data[self.level_index]["down-left"] = dl
            self.level_data[self.level_index]["up-right"] = ur

    def use_tool(self,tool):
        for i in self.tool_widgets:
            if i.cget("text") == tool:
                i.configure(bg="grey")
            else:
                i.configure(bg="white")
        self.tool = tool

    def open_another_window(self):
        # Create another window when the "Open Window" button is pressed
        if self.tool == "Pos":
            new_window = tk.Toplevel(self.root)
            new_window.title("PosPoints")
            elms = []
            i = 0
            for i,v in enumerate(self.pos_list):
                i_label = tk.Label(new_window, text=str(i+1))
                i_label.grid(row=i,column=0)
                label = tk.Label(new_window, text=f'{v["x"]} {v["y"]} <| {v["lat"]} {v["lon"]}')
                label.grid(row=i,column=1)

                def remove(ind):
                    self.pos_list.pop(ind)
                    new_window.destroy()

                bt = tk.Button(new_window, text=f'X', command=lambda ind=i : remove(ind))
                bt.grid(row=i,column=2)
                elms.append([i_label,label,bt])
            
            if len(self.pos_list) >= 2:
                res,get_pos = scale_map_calculate(self.pos_list,[self.img_width,self.img_height])
                self.get_pos = get_pos

                r = i + 1
                down_left = tk.Label(new_window, text=f'DL : {res[0]}')
                down_left.grid(row=r,column=0,columnspan=3)

                up_right = tk.Label(new_window, text=f'UR : {res[1]}')
                up_right.grid(row=r+1,column=0,columnspan=3)
        
        elif self.tool == "Mark":
            new_window = tk.Toplevel(self.root)
            new_window.title("MarkViewer")
            elms = []
            i = 0
            for i,v in enumerate(self.cords):
                i_label = tk.Label(new_window, text=str(v["name"]))
                i_label.grid(row=i,column=0)
                label = tk.Label(new_window, text=f'{v["x"]} {v["y"]} <| {v["lat"]} {v["lon"]}')
                label.grid(row=i,column=1)

                

                def remove(name):
                    for i,v2 in enumerate(self.cords):
                        if v2["name"] == name:
                            self.cords.pop(i)
                            break
                        
                    self.re_rendered()
                    new_window.destroy()

                bt = tk.Button(new_window, text=f'X', command=lambda name=v["name"]: remove(name))
                bt.grid(row=i,column=2)

                
                

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        level = simpledialog.askstring("Input", "Enter Level :")
        self.file_path = file_path

        self.level_data.append({"level":level,"filepath":file_path,"mark":[],"pos_cord":[],"down-left":[],"up-right":[]})

        if file_path:
            self.level_index = len(self.level_data) - 1
            self.current_level = self.level_data[self.level_index]["level"]
            self.file_path = self.level_data[self.level_index]["filepath"]


            self.cords = self.level_data[self.level_index]["mark"]
            self.pos_list = self.level_data[self.level_index]["pos_cord"]
            self.re_rendered()
            #self.set_image(file_path)

    def set_image(self, file_path):
        image = Image.open(file_path)
        image = Image.fromarray(trim_image(np.asarray(image)))
        self.image = ImageTk.PhotoImage(image)

        self.img_width, self.img_height = image.size
        self.canvas.config(scrollregion=(0, 0, self.img_width, self.img_height))
        self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)

    def draw_mark_on_canvas(self,name,img_x,img_y):
        #label = tk.Label(self.canvas, text=f"({name})", bg="white")
        #label.place(x=img_x, y=img_y)
        radius = 5
        self.canvas.create_oval(img_x - radius, img_y - radius, img_x + radius, img_y + radius, fill="blue")
        self.canvas.create_text(img_x, img_y-15, text=f"{name}", font=("Arial", 10))

    def re_rendered(self):
        self.set_image(self.file_path)
        # {"name": "Door", "lat": 0.5456608209516259, "lon": 0.3176369277874221, "x": 247.0, "y": 197.0}
        for ele in self.level_data[self.level_index]["mark"]:
            print(ele)
            self.draw_mark_on_canvas(ele["name"],ele["x"],ele["y"])

    def on_button_press(self, event):
        self.prev_x = event.x
        self.prev_y = event.y
        x,y = event.x+self.canvas.xview()[0]*self.img_width,event.y+self.canvas.yview()[0]*self.img_height

        if self.tool == "Pos":
            new_window = tk.Toplevel(self.root)
            new_window.title("Another Window")

            x_label = tk.Label(new_window,text="X")
            x_label.grid(row = 0, column = 0)
            x_entry = tk.Entry(new_window)
            x_entry.grid(row = 0, column = 1)

            x_entry.insert(0,str(x))

            y_label = tk.Label(new_window,text="Y")
            y_label.grid(row = 1, column = 0)
            y_entry = tk.Entry(new_window)
            y_entry.grid(row = 1, column = 1)

            y_entry.insert(0,str(y))

            lat_label = tk.Label(new_window,text="Latitude")
            lat_label.grid(row = 2, column = 0)
            lat_entry = tk.Entry(new_window)
            lat_entry.grid(row = 2, column = 1)

            lon_label = tk.Label(new_window,text="Longitude")
            lon_label.grid(row = 3, column = 0)
            lon_entry = tk.Entry(new_window)
            lon_entry.grid(row = 3, column = 1)

            def apply_btn():
                lat,lon,x,y = float(lat_entry.get()),float(lon_entry.get()),float(x_entry.get()),float(y_entry.get())

                self.pos_list.append({"lat":lat,"lon":lon,
                                      "x":x,"y":y})

                new_window.destroy()

            exec_button = tk.Button(new_window,text="Apply",command=apply_btn)
            exec_button.grid(row = 4, column = 0,columnspan=2)

        elif self.tool == "Mark" :#and self.get_pos is not None:
            if self.get_pos is not None:
                img_lat,img_lon = self.get_pos(x,y)
            else:
                if len(self.pos_list) >= 2:
                    res,get_pos = scale_map_calculate(self.pos_list,[self.img_width,self.img_height])
                    self.get_pos = get_pos
                    img_lat,img_lon = self.get_pos(x,y)
                else:
                    print("WARNING")
                    img_lat,img_lon = 0,0

            new_window = tk.Toplevel(self.root)
            new_window.title("Another Window")

            name_label = tk.Label(new_window,text="Name")
            name_label.grid(row = 0, column = 0)
            name_entry = tk.Entry(new_window)
            name_entry.grid(row = 0, column = 1)


            x_label = tk.Label(new_window,text="X")
            x_label.grid(row = 1, column = 0)
            x_entry = tk.Entry(new_window)
            x_entry.grid(row = 1, column = 1)

            x_entry.insert(0,str(x))

            y_label = tk.Label(new_window,text="Y")
            y_label.grid(row = 2, column = 0)
            y_entry = tk.Entry(new_window)
            y_entry.grid(row = 2, column = 1)

            y_entry.insert(0,str(y))

            lat_label = tk.Label(new_window,text="Latitude")
            lat_label.grid(row = 3, column = 0)
            lat_entry = tk.Entry(new_window)
            lat_entry.grid(row = 3, column = 1)

            lat_entry.insert(0,str(img_lat))

            lon_label = tk.Label(new_window,text="Longitude")
            lon_label.grid(row = 4, column = 0)
            lon_entry = tk.Entry(new_window)
            lon_entry.grid(row = 4, column = 1)

            lon_entry.insert(0,str(img_lon))

            def apply_btn():
                name,lat,lon,x,y = name_entry.get(),float(lat_entry.get()),float(lon_entry.get()),float(x_entry.get()),float(y_entry.get())

                self.cords.append({"name":name,"lat":lat,"lon":lon,
                                      "x":x,"y":y})
                self.re_rendered()

                new_window.destroy()

            exec_button = tk.Button(new_window,text="Apply",command=apply_btn)
            exec_button.grid(row = 5, column = 0,columnspan=2)

            
            

    def on_mouse_drag(self, event):
        if self.prev_x and self.prev_y and self.tool=="Pan":
            dx = event.x - self.prev_x
            dy = event.y - self.prev_y

            self.left_top["y"] -= dy
            self.left_top["x"] -= dx

            self.canvas.scan_mark(0, 0)
            self.canvas.scan_dragto(dx, dy, gain=1)
            self.prev_x = event.x
            self.prev_y = event.y

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewer(root)
    app.run()
