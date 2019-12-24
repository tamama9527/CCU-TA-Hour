from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QPushButton, QGroupBox, QLabel, QMessageBox

from ta import Ui_MainWindow
import sys
import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
import qdarkstyle

month_dict = {'一月': 1, '二月': 2, '三月': 3, '四月': 4, '五月': 5, '六月': 6, '七月': 7, '八月': 8, '九月': 9, '十月': 10, '十一月': 11,
              '十二月': 12}


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.initUI()
        self.session = requests.session()

    def initUI(self):
        self.ui.account.setTabOrder(self.ui.account,self.ui.password)
        self.ui.calendarWidget.selectionChanged.connect(self.dateDisplay)
        self.ui.loginbutton.clicked.connect(self.login)
        self.ui.generate.clicked.connect(self.generate)
        # self.ui.projectGroup.setVisible(False)

    def dateDisplay(self):
        date = self.ui.calendarWidget.selectedDate().toString().split(' ')
        year = int(date[3])
        day = int(date[2])
        month = int(month_dict[date[1]])
        chinese_date = '/'.join((str(year), str(month), str(day)))
        self.ui.date.setText(chinese_date)

    def login(self):
        if self.ui.account.text() is not '' and self.ui.password.text() is not '':
            account = self.ui.account.text()
            password = self.ui.password.text()
            # 1:計畫主持人,2:專任助理,3:兼任助理,4:臨時工
            account_type = self.ui.account_type.currentIndex() + 1
            LoginData = {'staff_cd': account, 'passwd': password, 'proj_type': account_type}
            response = self.session.post('https://miswww1.ccu.edu.tw/pt_proj/control.php',LoginData ,allow_redirects=False)
            response.encoding='utf-8'
            if response.status_code is 200:
                soup = bs(response.text,'lxml')
                msg = QMessageBox.information(self, '錯誤', soup.find('center').contents[0], QMessageBox.Ok)
                return
            self.ui.frame.setEnabled(False)
            self.setFixedSize(289, 709)
            self.moveToCenter()
            self.session.get('https://miswww1.ccu.edu.tw/pt_proj/control2.php')
            response = self.session.get('https://miswww1.ccu.edu.tw/pt_proj/main2.php')
            response.encoding = 'utf-8'
            soup = bs(response.text.encode('utf-8'), 'lxml')
            allProject = soup.findAll('option')
            for i in allProject:
                print(i.string)
                projectNumber,projectName = i.string.split(' ')
                self.ui.projectname.addItem(projectName,projectNumber)
        else:
            msg = QMessageBox.information(self, '錯誤', '帳號密碼不為空', QMessageBox.Ok)

    def generate(self):
        totalTime = int(self.ui.totalhours.text())
        projectNumber = self.ui.projectname.currentData()
        startTime = self.ui.date.text()
        workDetail = self.ui.plainTextEdit.toPlainText()
        now = datetime.strptime(startTime,'%Y/%m/%d')
        dataCount = 0
        hours = 8
        print(now)
        while totalTime != 0:
            if now.weekday()>4:
                addDay = 7 - now.weekday()
                now = now + timedelta(days=addDay)
            else:
                if totalTime < hours:
                    hours = totalTime
                postData = {'type': projectNumber, 'yy': str(now.year - 1911), 'mm': str(now.month),
                            'dd': str(now.day), 'hrs': str(hours), 'workin': workDetail}
                self.session.post('https://miswww1.ccu.edu.tw/pt_proj/next.php', postData)
                # 不get此頁面，後續功能好像會出錯
                r = self.session.get('https://miswww1.ccu.edu.tw/pt_proj/xa2.php')
                r.encoding='utf-8'
                print(r.text)
                totalTime = totalTime - hours
                now = now + timedelta(days=1)
                dataCount += 1
        # todb.php不吃session，所以一定要餵cookie給他
        cookies = {'PHPSESSID': self.session.cookies['PHPSESSID']}
        print(cookies)
        r = requests.get('https://miswww1.ccu.edu.tw/pt_proj/todb.php', cookies=cookies)
        # 條件搜尋日誌
        print()
        data = {'unit_cd1': projectNumber, 'sy': str(now.year-1911), 'sm': str(now.month), 'sd': '01', 'ey': str(now.year-1911), 'em': str(now.month),
                'ed': '30', 'go': u'依條件選出資料'}
        print(data)
        r = self.session.post('https://miswww1.ccu.edu.tw/pt_proj/print_row.php', data=data)
        r.encoding='utf-8'
        print(r.text)
        # 產生批號
        printData = {}
        printData['chka'] = '1'
        printData['go_check'] = '確定送出並列印'
        for i in range(dataCount):
            name = 'cb_{}'.format(i)
            printData['cb_{}'.format(i)] = '1'
            printData['ssno_{}'.format(i + 1)] = '1'
        print(printData)
        r = self.session.post('https://miswww1.ccu.edu.tw/pt_proj/print_check.php', data=printData)
        r.encoding = 'utf-8'
        print(r.text)
        soup = bs(r.text, 'lxml')
        print(soup.find('u').string)
        self.ui.output_number.setText(soup.find('u').string)
        return

    def moveToCenter(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(
            QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
