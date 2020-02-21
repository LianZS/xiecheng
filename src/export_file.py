import xlrd, xlwt, csv, os
from enum import Enum
from xlutils.copy import copy


class FileType(Enum):
    CSV = 'csv'
    XLS = 'xls'
    XLSX = 'xlsx'


class FileModel(Enum):
    ADD = 'add_write'
    WB = 'write'


class ExportFile(object):
    __data_file__ = None  # 文件实例
    row = 0  # 行数
    worksheet: xlwt.Worksheet = None  # 表
    add_adjust = False  # 用来判断是否获取过一次行数

    def __init__(self, file_name: str, file_type: FileType, write_model: FileModel = FileModel.WB):
        """

        :param file_name:文件名
        :param file_type:文件类型
        :param write_model:写入方式：追加和覆盖
        """
        self.file_type = file_type
        self.file_name = ''.join([file_name, '.', file_type.value])
        self.write_model = write_model
        if write_model == FileModel.ADD:
            self.add_adjust = True  # 可以获取文本行数

    def write_to_file(self, data: list, sheet_name='My Worksheet'):
        if self.file_type == FileType.XLS or self.file_type == FileType.XLSX:
            if self.__data_file__ is None:
                self.__data_file__ = xlwt.Workbook(encoding='ascii')
                self.worksheet = self.__data_file__.add_sheet(sheetname=sheet_name)
            if self.file_type == FileType.XLS:

                for c, label in enumerate(data):
                    self.__write_to_xls__(self.row, c, label)
            elif self.file_type == FileType.XLSX:
                for c, label in enumerate(data):
                    self.__write_to_xlsx__(self.row, c, label)
        else:
            pass

    def add_data(self, data: list, sheet_name=None):
        """
        在文件原有数据基础上进行追加
        :param data: 数据列表
        :return:
        """
        if self.file_type == FileType.XLS or self.file_type == FileType.XLSX:
            if not os.path.exists(self.file_name):
                if sheet_name is None:
                    self.write_to_file(data)
                else:
                    self.write_to_file(data, sheet_name)
                self.save()
                return

            if self.add_adjust:  # 确保文件只读取复制一次
                book = xlrd.open_workbook(self.file_name)
                self.__data_file__ = copy(book)  # 完成xlrd对象向xlwt对象转换
                if sheet_name is None:
                    sheet = book.sheet_by_index(0)
                    self.worksheet = self.__data_file__.get_sheet(0)

                else:
                    try:
                        sheet = book.sheet_by_name(sheet_name)
                        self.worksheet = self.__data_file__.get_sheet(sheet_name)

                    except xlrd.XLRDError:
                        sheet = book.sheet_by_index(0)
                        self.worksheet = self.__data_file__.get_sheet(0)
                self.row = sheet.nrows  # 获得行数
                self.add_adjust = False  # 后面的追加操作不能再读取行数了。

            if sheet_name is None:
                self.write_to_file(data)
            else:

                self.write_to_file(data, sheet_name)

    def __write_to_xls__(self, row, colum, label):
        """
        写入xls
        :param row: 第几行
        :param colum: 第几列
        :param label: 数据
        :return:
        """
        self.worksheet.write(row, colum, label)
        self.row += 1

    def __write_to_xlsx__(self, row, colum, label):
        """
        写入xls
        :param row: 第几行
        :param colum: 第几列
        :param label: 数据
        :return:
        """
        self.worksheet.write(row, colum, label)
        self.row += 1

    def __write_to_csv__(self, row, colum, label):
        """
        写入xls
        :param row: 第几行
        :param colum: 第几列
        :param label: 数据
        :return:
        """
        pass

    def save(self):
        """
        保存数据
        :return:
        """
        self.__data_file__.save(self.file_name)


