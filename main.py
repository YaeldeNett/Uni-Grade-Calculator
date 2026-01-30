from ui import App, create_root

             
# Main entry point to setup and run the application
def main():
    root = create_root()
    app = App(root)
    root.geometry("1280x720")
    root.minsize(1024, 675)
    root.mainloop()

if __name__ == "__main__":
    main()
