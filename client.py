import tkinter as tk
from tkinter import colorchooser
from customtkinter import *
from PIL import Image, ImageDraw
import threading
import socket
import pickle

class clientNetwork:
    def __init__(self,host,port) -> None:
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.connect((host,port))
    
    def loop(self,stack):
        print(stack)
        self.socket.send(pickle.dumps(stack))
        return pickle.loads(self.socket.recv(1000))

class WhiteboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whiteboard")
        self.socket = clientNetwork('localhost',8080)
        
        self.canvas_width = 800
        self.canvas_height = 600

        self.sidebar_frame = tk.Frame(root)
        self.sidebar_frame.grid(row=0, column=0)

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.grid(row=0, column=1)

        self.user_text = CTkLabel(self.sidebar_frame, text="Whiteboard", text_color="black", font=("", 25), anchor="n")
        self.user_text.grid(row=0, column=0, columnspan=2, padx=20, pady=40, sticky="n")

        self.draw_button = CTkButton(self.sidebar_frame, text="Draw", command=self.start_draw, font=("", 18), border_spacing=8, fg_color="black")
        self.draw_button.grid(row=1, column=0, padx=20)

        self.erase_button = CTkButton(self.sidebar_frame, text="Erase", command=self.start_erase, font=("", 18), border_spacing=8, fg_color="black")
        self.erase_button.grid(row=2, column=0, padx=20, pady=20)

        self.clear_button = CTkButton(self.sidebar_frame, text="Clear", command=self.clear_canvas, font=("", 18), border_spacing=8, fg_color="black")
        self.clear_button.grid(row=3, column=0, padx=20)

        self.choose_color_button = CTkButton(self.sidebar_frame, text="Choose Color", command=self.choose_color, font=("", 18), border_spacing=8, fg_color="black")
        self.choose_color_button.grid(row=4, column=0, padx=20, pady=20)

        self.save_button = CTkButton(self.sidebar_frame, text="Save", font=("", 18), border_spacing=8, fg_color="black", command=self.save_drawing)
        self.save_button.grid(row=5, column=0, padx=10, pady=(0,20))

        self.size_slider = CTkSlider(self.sidebar_frame, from_=20, to=1 , orientation="vertical", command=self.size_slider_event, button_color="black", button_hover_color="black")
        self.size_slider.grid(row=1, column=1, rowspan=4, padx=20, sticky="ns")
        self.size_slider.set(5)

        self.brush_selector_text = CTkLabel(self.sidebar_frame, text="Brush Type:", text_color="black", font=("", 20))
        self.brush_selector_text.grid(row=6, column=0, padx=20, pady=(0,10), sticky="w")

        self.brush_selector = CTkComboBox(self.sidebar_frame, values=["Brush", "Marker", "Pencil", "Pen"], command=self.brush_select, font=("", 18), fg_color="black", height=40, state="readonly")
        self.brush_selector.grid(row=7, column=0, padx=20, pady=(0,30), columnspan=2, sticky="nsew")
        self.brush_selector.set("Brush")

        self.brush_size_text = CTkLabel(self.sidebar_frame, text="Brush\nSize", text_color="black", font=("", 18))
        self.brush_size_text.grid(row=5, column=1, padx=20, pady=10, sticky="ns")


         # Initialize an empty image for saving the drawing
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)
        
        self.drawing = False
        self.erasing = False
        self.last_x, self.last_y = None, None

        self.canvas.bind("<Button-1>", self.start_action)
        self.canvas.bind("<B1-Motion>", self.draw_or_erase)
        self.canvas.bind("<ButtonRelease-1>", self.stop_action)

        self.brush_width = 5
        self.brush_color = 'black'
        self.background_color = 'white'
        self.brush_type = "Brush"
        self.send_stack = []

        threading.Thread(target=self.dataLoop).start()

    def start_action(self, event):
        if self.drawing:
            self.start_draw(event)
        elif self.erasing:
            self.start_erase(event)

    def stop_action(self, event):
        if self.drawing:
            self.stop_draw(event)
        elif self.erasing:
            self.stop_erase(event)

    def start_draw(self, event=None):
        self.drawing = True
        self.erasing = False
        if event:
            self.last_x, self.last_y = event.x, event.y

    def stop_draw(self, event=None):
        self.drawing = False
        self.erasing = False

    def start_erase(self, event=None):
        self.erasing = True
        self.drawing = False
        if event:
            self.last_x, self.last_y = event.x, event.y

    def stop_erase(self, event=None):
        self.erasing = False
        self.drawing = False

    def draw_or_erase(self, event):
            x, y = event.x, event.y
            if self.drawing:
                if self.brush_type == "Brush":
                    self.send_stack.append(((self.last_x,self.last_y,x,y),(self.brush_color,self.brush_width,self.brush_type),"drawing"))
                    self.canvas.create_line((self.last_x, self.last_y, x, y), fill=self.brush_color, width=self.brush_width * 2, capstyle=tk.ROUND, smooth=True)
                    self.draw.line((self.last_x, self.last_y, x, y), fill=self.brush_color, width=self.brush_width * 2)
            
                elif self.brush_type == "Marker":
                    self.send_stack.append(((self.last_x,self.last_y,x,y),(self.brush_color,self.brush_width,self.brush_type),"drawing"))
                    self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_width * 3, fill=self.brush_color, stipple="gray50", capstyle=tk.PROJECTING, smooth=False)
                    self.draw.line((self.last_x, self.last_y, x, y), fill=self.brush_color, width=self.brush_width * 3)
                
                elif self.brush_type == "Pencil":
                    self.send_stack.append(((self.last_x,self.last_y,x,y),(self.brush_color,self.brush_width,self.brush_type),"drawing"))
                    for i in range(self.brush_width):
                        self.canvas.create_line(self.last_x - i, self.last_y - i, x - i, y - i, width=1, fill=self.brush_color, smooth=False)
                        self.draw.line((self.last_x - i, self.last_y - i, x - i, y - i), fill=self.brush_color, width=1)
                
                elif self.brush_type == "Pen":
                    self.send_stack.append(((self.last_x,self.last_y,x,y),(self.brush_color,self.brush_width,self.brush_type),"drawing"))
                    self.canvas.create_line(self.last_x, self.last_y, x, y, width=self.brush_width // 2, fill=self.brush_color, capstyle=tk.ROUND, smooth=True)
                    self.draw.line((self.last_x, self.last_y, x, y), fill=self.brush_color, width=self.brush_width // 2)
                
                
                self.last_x, self.last_y = x, y
            
            elif self.erasing:
                x, y = event.x, event.y
                self.send_stack.append(((self.last_x,self.last_y,x,y),(self.brush_color,self.brush_width,self.brush_type),"erasing"))
                self.canvas.create_rectangle(x - self.brush_width, y - self.brush_width, x + self.brush_width, y + self.brush_width, fill=self.background_color, outline="white")

    def clear_canvas(self):
        self.canvas.delete("all")
        # resetting image for a new save
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)

    def choose_color(self):
        self.color_code = colorchooser.askcolor(title ="Choose color")
        self.brush_color = self.color_code[1]

    def size_slider_event(self, value):
        self.brush_width = int(value)

    def brush_select(self, choice):
        self.brush_type = choice

    def dataLoop(self):
        while True:
            recv_stack = self.socket.loop(self.send_stack)
            self.send_stack = []
            while recv_stack:
                obj = recv_stack.pop()
                print(obj)
                if obj[2] == "drawing":
                    if obj[1][2] == "Brush":
                        self.canvas.create_line(obj[0],fill=obj[1][0],width=obj[1][1] * 2, capstyle=tk.ROUND, smooth=True)
                        self.draw.line(obj[0], fill=obj[1][0], width=obj[1][1] * 2)

                    elif obj[1][2] == "Marker":
                        self.canvas.create_line(obj[0],fill=obj[1][0],width=obj[1][1] * 3, stipple="gray50", capstyle=tk.PROJECTING, smooth=False)
                        self.draw.line(obj[0], fill=obj[1][0], width=obj[1][1] * 3)

                    elif obj[1][2] == "Pen":
                        self.canvas.create_line(obj[0],fill=obj[1][0],width=obj[1][1] // 2, capstyle=tk.ROUND, smooth=True)
                        self.draw.line(obj[0], fill=obj[1][0], width=obj[1][1] // 2)

                    elif obj[1][2] == "Pencil":
                        for i in range(obj[1][1]):
                            self.canvas.create_line(obj[0][0] - i, obj[0][1] - i, obj[0][2] - i, obj[0][3] - i, width=1, fill=obj[1][0], smooth=False)
                            self.draw.line((obj[0][0] - i, obj[0][1]- i, obj[0][2] - i, obj[0][3] - i), fill=obj[1][0], width=1)
                
                elif obj[2] == "erasing":
                    self.canvas.create_rectangle(obj[0][2] - obj[1][1], obj[0][3] - obj[1][1], obj[0][2] + obj[1][1], obj[0][3] + obj[1][1], fill="white", outline="white")




    def save_drawing(self):
        file_path = "whiteboard_drawing.png"
        self.image.save(file_path)
        print(f"Image saved as {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WhiteboardApp(root)
    root.mainloop()
