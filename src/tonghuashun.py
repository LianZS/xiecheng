import requests, re, json
from src.export_file import *


class FundTrend(Enum):
    """
    涨跌情况表
    """
    SUPER_ROSE = [4, 5]
    VERY_ROSE = [3, 4]
    MUCH_ROSE = [2, 3]
    ROSE = [1, 2]
    SMALL_ROSE = [0, 1]
    SUPER_FALL = [-4, -5]
    VERTY_FALL = [-3, -4]
    MUCH_FALL = [-2, -3]
    FALL = [-1, -2]
    SMALL_FALL = [0, -1]


class FundCodeInfo(object):
    def __init__(self, c1, c2):
        self.fund_code = c1
        self.spceial_code = c2


class FundInfo(object):

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
        }
        self.xlsx = None

    def get_all_fund_base_info(self, url=None):
        if url is None:
            url = 'http://fund.10jqka.com.cn/hqcode.js'
        response = requests.get(url=url, headers=self.headers)
        if response.status_code == 200:
            result = re.sub('var hqjson=', '', response.text)
        else:
            result = None
        if result:
            fund_code_info: dict = json.loads(result)
            for fund_code, special_code in fund_code_info.items():
                yield FundCodeInfo(fund_code, special_code)

    def get_func_info(self, fund_code) -> list:
        response = requests.get(url='http://fund.10jqka.com.cn/data/client/myfund/' + fund_code, headers=self.headers)
        if response.status_code == 200:
            result = json.loads(response.text)
        else:
            result = None
        if result:
            data = result.get('data')
            if data:
                data = data[0]
                fund_info_list = list()
                fund_name = data.get('name')  # 基金
                fund_info_list.append(fund_name)
                fund_info_list.append(fund_code)
                hqcode = data.get('hqcode')  # 信息代码
                fund_info_list.append(hqcode)
                fundtype = data.get('fundtype')  # 基金类型
                fund_info_list.append(fundtype)
                levelOfRisk = data.get('levelOfRisk')  # 风险程度
                fund_info_list.append(levelOfRisk)
                themeList = data.get('themeList')  # 投资主题
                for theme in themeList:
                    theme_name = theme.get('field_name')
                    fund_info_list.append(theme_name)
                return fund_info_list

    def get_realtime_rate(self, special_code, low_rate):
        response = requests.get(
            url='http://gz-fund.10jqka.com.cn/?module=api&controller=index&action=chart&info=vm_fd_{0}&start=0930'.format(
                special_code), headers=self.headers)
        if response.status_code == 200:
            result = re.search('~(\d{4}.*)', response.text)
            if result:
                result = result.group(1)
                valuation_info = result.split(';')
                sum = 0
                count = 0
                for valuation in valuation_info:
                    info = valuation.split(',')
                    realtime = info[0]
                    now_valuation = float(info[1])
                    yesterday_valuation = float(info[2])
                    difference = (now_valuation - yesterday_valuation) / yesterday_valuation * 100
                    sum += difference
                    count += 1
                relative_rate = sum / count
                if low_rate.value[0] < 0:
                    if low_rate.value[1] <= relative_rate < low_rate.value[0]:
                        return (True, relative_rate)

                    else:
                        return (False, relative_rate)
                else:
                    if low_rate.value[0] <= relative_rate < low_rate.value[1]:
                        return (True, relative_rate)

                    else:
                        return (False, relative_rate)


            else:
                return (False, None)
        else:
            return (False, None)

    def write_info(self, info_list: list, filename: str, filetype: FileType):
        if self.xlsx is None:
            self.xlsx = ExportFile(filename, filetype, FileModel.ADD)
        max_for = 40
        for item in info_list:
            self.xlsx.add_row(item)
            max_for -= 1
            if max_for == 0:
                self.xlsx.save()
                max_for = 40
        self.xlsx.save()
