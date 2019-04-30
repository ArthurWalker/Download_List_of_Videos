import PyQt5
from PyQt5.QtWidgets import QApplication,QWidget,QPushButton,QVBoxLayout

def main():
    # Instantiate an Application. A requirement of QT (every GUI app must have exactly 1 instance of QApplication)
    app = QApplication([])

    # Create a window. It acts as a container
    window = QWidget()

    # Create a layout
    layout = QVBoxLayout()

    # Add 2 buttons
    layout.addWidget(QPushButton('Top'))
    layout.addWidget(QPushButton('Bottom'))

    # Tell the window to use this layout
    window.setLayout(layout)
    window.show()

    # Run the application until the user closes it
    app.exec_()

if __name__=='__main__':
    main()

    # def check_existed_ID_download(video_ID):
    #     with open('.json') as json_file:
    #         data = json.load(json_file)
    #         if video_ID not in data['downloaded_ID']:
    #             return 'Existed'
    #     return 'Not existed'
    #
    # def check_prev_download():
    #     with open('.json') as json_file:
    #         data = json.load(json_file)
    #     havent_download_ID = list(set(video_id_playlist) - set(data['downloaded_ID']))
    #     if len(havent_download_ID) > 0:
    #         return True,havent_download_ID
    #     return False,[]