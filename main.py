import os
from modules import SystemWilddog

#-----------------------------------------------------------
def main():
    wd = SystemWilddog()
    wd.run()


#-----------------------------------------------------------
if __name__ == "__main__":
    os.system("clear")
    main()