import xlrd, xlwt, csv, os
from io import TextIOWrapper
from enum import Enum
from xlutils.copy import copy


class FileType(Enum):
    CSV = 'csv'
    XLS = 'xls'
    XLSX = 'xlsx'


class FileModel(Enum):
    ADD = 'add_write'
    WB = 'write'
    RB = 'read'


class ExportFile(object):
    __data_file__ = None  # 文件实例
    row = 0  # 行数
    __worksheet__ = None  # 表
    __copy_adjust__ = False  # 用来判断是否获取过一次行数

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
            self.__copy_adjust__ = True  # 可以获取文本行数

    def write_to_file(self, data: list, sheet_name: str = 'My Worksheet'):
        if self.file_type == FileType.XLS or self.file_type == FileType.XLSX:
            if self.__data_file__ is None:
                self.__data_file__ = xlwt.Workbook(encoding='ascii')
                self.__worksheet__ = self.__data_file__.add_sheet(sheetname=sheet_name)
            if self.file_type == FileType.XLS:

                for c, label in enumerate(data):
                    self.__write_to_xls__(self.row, c, label)
            elif self.file_type == FileType.XLSX:
                for c, label in enumerate(data):
                    self.__write_to_xlsx__(self.row, c, label)
            self.row += 1
        elif self.file_type == FileType.CSV:
            if self.__data_file__ is None:
                if os.path.exists(self.file_name):

                    if self.write_model == FileModel.ADD:
                        self.__data_file__ = open(self.file_name, mode='a+', newline='')
                    elif self.write_model == FileModel.WB:
                        self.__data_file__ = open(self.file_name, mode='w+', newline='')
                    self.__worksheet__ = csv.writer(self.__data_file__)

                else:
                    open(self.file_name, 'x').close()
                    self.write_to_file(data, sheet_name)
                    return
            self.__write_to_csv__(data)

    def add_row(self, data: list, sheet_name: str = None):
        """
        在文件原有数据基础上进行追加
        :param data: 数据列表
        :return:
        """
        # 判断文件是否已经存在，不存在则创建后写入
        if not os.path.exists(self.file_name):
            if sheet_name is None:
                self.write_to_file(data)
            else:
                self.write_to_file(data, sheet_name)
            self.save()
            return
        if self.file_type == FileType.XLS or self.file_type == FileType.XLSX:

            if self.__copy_adjust__:  # 确保文件只读取复制一次
                book = xlrd.open_workbook(self.file_name)
                self.__data_file__: xlwt.Workbook = copy(book)  # 完成xlrd对象向xlwt对象转换
                if sheet_name is None:
                    sheet = book.sheet_by_index(0)
                    self.__worksheet__ = self.__data_file__.get_sheet(0)

                else:
                    try:
                        sheet = book.sheet_by_name(sheet_name)
                        self.__worksheet__ = self.__data_file__.get_sheet(sheet_name)

                    except xlrd.XLRDError:
                        sheet = book.sheet_by_index(0)
                        self.__worksheet__ = self.__data_file__.get_sheet(0)
                self.row = sheet.nrows  # 获得行数
                self.__copy_adjust__ = False  # 后面的追加操作不能再读取行数了。

        elif self.file_type == FileType.CSV:
            if self.__copy_adjust__:  # 确保文件只读取复制一次
                # 读取行数
                with open(self.file_name, mode='r') as r:
                    self.row = len([i for i in csv.reader(r)])

                if self.write_model == FileModel.ADD:
                    self.__data_file__: TextIOWrapper = open(self.file_name, mode='a+', newline='')
                elif self.write_model == FileModel.WB:
                    self.__data_file__: TextIOWrapper = open(self.file_name, mode='w+', newline='')
                self.__worksheet__ = csv.writer(self.__data_file__)
                self.__copy_adjust__ = False

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
        self.__worksheet__.write(row, colum, label)
        self.row += 1

    def __write_to_xlsx__(self, row, colum, label):
        """
        写入xls
        :param row: 第几行
        :param colum: 第几列
        :param label: 数据
        :return:
        """
        self.__worksheet__.write(row, colum, label)

    def __write_to_csv__(self, data: list):
        """
        写入csv文件
        :param data:数据列表
        :return:
        """
        self.__worksheet__.writerow(data)

    def save(self):
        """
        保存数据
        :return:
        """
        if self.file_type == FileType.XLS or self.file_type == FileType.XLSX:

            self.__data_file__.save(self.file_name)

        elif self.file_type == FileType.CSV:
            if not self.__copy_adjust__:
                self.__data_file__.close()

    @property
    def fieldnames(self):
        return self.__data_file__

    @fieldnames.setter
    def fieldnames(self, value):
        """

        :param value: xlwt.Workbook类型或者TextIOWrapper类型
        :return:
        """
        self.__data_file__ = value

    @fieldnames.getter
    def fieldnames(self):
        if isinstance(self.__data_file__, TextIOWrapper):
            return self.__data_file__.name
        elif isinstance(self.__data_file__, xlwt.Workbook):
            return self.file_name

    def read_rows(self, start_colx=0, end_colx=None, sheetname: str = None):
        if self.file_type == FileType.XLSX or self.file_type == FileType.XLS:
            book = xlrd.open_workbook(self.file_name)
            if sheetname is None:
                table = book.sheet_by_index(0)
            else:
                table = book.sheet_by_name(sheetname)
            if end_colx is None:
                end_colx = table.nrows
            for i in range(start_colx, end_colx):
                yield table.row_values(i)
