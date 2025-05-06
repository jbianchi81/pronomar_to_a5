from ftplib import FTP
import yaml
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config/default.yml")
config = yaml.load(open(config_path,"r",encoding="utf-8"),Loader=yaml.CLoader)

def getPronoFile():
    # Connect and login to FTP server
    ftp = FTP(config["source"]["host"])
    ftp.login(user=config["source"]["user"], passwd=config["source"]["password"])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_file_path = os.path.join(script_dir, config["source"]["local_file_path"])
    # Open a local file to save the downloaded content
    with open(local_file_path, 'wb') as f:
        ftp.retrbinary(f'RETR {config["source"]["remote_file_path"]}', f.write)

    # Close the FTP connection
    ftp.quit()

    print(f"File downloaded to {local_file_path}")

if __name__ == "__main__":
    getPronoFile()