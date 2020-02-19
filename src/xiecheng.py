import requests
import re
from urllib import parse
import abc
from bs4 import BeautifulSoup
from types import GeneratorType


class SingleComment(object):
    __slots__ = ['author', 'star', 'comment', 'date_published']

    def __init__(self, author: str, star: int, comment: str, date_published: str):
        self.author = author
        self.star = star
        self.comment = comment
        self.date_published = date_published

    def __str__(self):
        return "作者：{author},评分：{star}, 发布日期：{date_published},评论内容：{comment}".format_map(
            {'author': self.author, 'star': self.star, 'date_published': self.date_published, 'comment': self.comment})


class CommentView(object):
    """
    获取景区评论数据
    """
    poi_id = 1
    district_name = ''
    district_id = 1
    page_now = 1
    resource_id = 1

    def __init__(self, user_agent=None, cookie=None):
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko)" \
                         " Chrome/69.0.3497.100 Safari/537.36"
        self.headers = {
            'user-agent': user_agent,
            'cookie': cookie
        }

    def get_comment_detail(self, url):
        response = requests.get(url=url, headers=self.headers)
        self.poi_id = int(re.search('poiid\D+(\d+)"', response.text).group(1))
        self.district_name = re.search('sight/([a-zA-Z]+)\d', url).group(1).capitalize()
        self.district_id = int(re.search('sight/[a-zA-Z]+(\d+)\D', url).group(1))
        self.resource_id = int(re.search('\d+/(\d+)\Shtml', url).group(1))
        self.page_now = 1
        return self.__get_comment_view__(self.poi_id, self.district_id, self.district_name, self.page_now,
                                         self.resource_id)

    def __get_comment_view__(self, poi_id: int, district_id: int, district_name: str, page_now: int,
                             resource_id: int) -> GeneratorType:
        """

        获取评论数据，包括作者,评论内容，评分，评论时间
        :param poi_id:
        :param district_id:城市id
        :param district_name:城市名，拼音首字母大写，如Guangzhou
        :param page_now:评论分页
        :param resource_id:景区id
        :return:SingleComment的GeneratorType
        """

        post_data = {
            'poiID': poi_id,
            'districtId': district_id,
            'districtEName': district_name,
            'pagenow': page_now,
            'resourceId': resource_id,
        }

        response = requests.post(url='https://you.ctrip.com/destinationsite/TTDSecond/SharedView/AsynCommentView',
                                 data=post_data,
                                 headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        sight_commentbox = soup.find(name='div', class_='comment_ctrip')
        for comment_single in sight_commentbox.children:
            if len(comment_single) > 2:
                author: str = comment_single.find(name='a', attrs={'itemprop': 'author'}).text
                star: str = comment_single.find(name='span', class_='starlist').find(name='span').attrs['style']
                comment: str = comment_single.find(name='span', class_='heightbox').text
                date_published: str = comment_single.find(name='em', attrs={'itemprop': 'datePublished'}).text
                star: int = int(re.match('\D+(\d+)', star).group(1)) / 20
                yield SingleComment(author, star, comment, date_published)

    def next_page(self):
        """翻页功能"""
        self.page_now += 1
        return self.__get_comment_view__(self.poi_id, self.district_id, self.district_name, self.page_now,
                                         self.resource_id)


class TabInfo(object):
    __slots__ = ['tab', 'url_entrance', 'num']

    def __init__(self, tab: str, url_entrance: str, num: int):
        """

        :param tab: 标签
        :param url_entrance:标签内容链接入口
        :param num:相关结果数量

        """
        self.tab = tab
        self.url_entrance = url_entrance
        self.num = num

    def __str__(self):
        return "{tab:5}\t{num:5}\t{url_entrance:20}".format_map(
            {'tab': self.tab, 'url_entrance': self.url_entrance, 'num': self.num})


class AttractionInfo(object):
    __slots__ = ['url', 'name']

    def __init__(self, url: str, name: str):
        """
        :param url:景区资料链接
        :param name: 景区名字
        """
        self.url = url
        self.name = name

    def __str__(self):
        return "{name:30}{url:20}".format_map({'name': self.name, 'url': self.url})


class CityVacationsAdView(object):
    """
    获取城市景点
    """
    CityVacationsView = None

    class ResponseInfo(object):
        """
        请求响应体
        """

        def __init__(self, response: requests.Response, tab_map: dict, domain: str):
            """
            :param response: 请求响应体
            :param tab_map:响应标签信息，存储格式{序号:TabInfo}
            :param domain:域名
            """
            self.response = response
            self.domain = domain
            self.tab_map = tab_map

        def __str__(self):
            list_info = list()
            list_info.append("{:5}\t{:5}\t{:5}\t{:20}\n".format("序号", "标签", "数量", "详情链接"))

            for i, value in enumerate(self.tab_map.values()):
                list_info.append("{key:^5}\t{tabInfo}\n ".format_map({'key': i, 'tabInfo': value}))
            return ''.join(list_info)

    def __init__(self, user_agent=None, cookie=None):
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko)" \
                         " Chrome/69.0.3497.100 Safari/537.36"
        self.headers = {
            'user-agent': user_agent,
            'cookie': cookie
        }

    def __get_request_response__(self, search_keyword: str) -> ResponseInfo:
        """
        发送搜索请求
        :param search_keyword: 搜索关键词
        :return:
        """
        href = 'https://you.ctrip.com/SearchSite/?'
        paramer = {
            'query': search_keyword
        }
        url = href + parse.urlencode(paramer)
        response = requests.get(url=url, headers=self.headers)
        res = parse.urlparse(response.url)
        domain = ''.join([res.scheme, '://', res.netloc])  # 域名
        # 提取搜索结果标签信息
        soup = BeautifulSoup(response.text, 'lxml')
        ul_tag = soup.find(name='ul', class_='list-tabs')
        tab_map = dict()  # 存储标签信息
        for i, li_tag in enumerate(ul_tag.children):
            if len(li_tag) <= 1:
                continue
            a_tag = li_tag.find(name='a')
            href = ''.join([domain, a_tag.attrs['href']])  # 标签内容入口
            tab_info = re.sub('\s', '', a_tag.text)  # 标签信息
            temp = re.match("(\D+)(\d+)", tab_info)
            tab = temp.group(1)  # 标签
            result_num = int(temp.group(2))  # 此类标签搜索结果数目
            tab_map[tab] = TabInfo(tab, href, result_num)

        return self.ResponseInfo(response, tab_map, domain)

    def get_search_result(self, search_keyword: str):
        """
        获取搜索结果
        :return:
        """
        return self.__get_request_response__(search_keyword)

    def select_tab(self, tab):
        pass


class ListView(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def show_vacations_list(self, vacations_list):
        pass

    @abc.abstractmethod
    def next_page(self):
        pass

    @abc.abstractmethod
    def before_page(self):
        pass


class AttractionListView(ListView):
    __page = 1
    __keyword_query = None
    __request_url = None

    def __init__(self, user_agent=None, cookie=None):
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko)" \
                         " Chrome/69.0.3497.100 Safari/537.36"
        self.headers = {
            'user-agent': user_agent,
            'cookie': cookie
        }

    def get_vacations_url_entrance(self, search_keyword: str):
        """
        搜索关键词相关的景点
        :param search_keyword:
        :return:
        """
        response_info = CityVacationsAdView().get_search_result(search_keyword)
        vacation_info: TabInfo = response_info.tab_map.get('景点')
        url = vacation_info.url_entrance
        res = parse.urlparse(url)
        self.__request_url = ''.join([res.scheme, "://", res.netloc, res.path, '/?'])
        self.__keyword_query = parse.parse_qs(res.query)['query'][0]

        return self.__get_vacations_list__()

    def __get_vacations_list__(self) -> GeneratorType:
        """
        获取相关景区列表
        :param url:
        :return:
        """
        parameters = {
            'query': self.__keyword_query,
            'isAnswered': '',
            'isRecommended': '',
            'publishDate': '',
            'PageNo': self.__page
        }
        url = self.__request_url + parse.urlencode(parameters)
        response = requests.get(url=url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        ul_tag = soup.find(name='ul', class_='jingdian-ul')

        res = parse.urlparse(response.url)
        domain = ''.join([res.scheme, '://', res.netloc])  # 域名
        for li_tag in ul_tag.children:
            if len(li_tag) <= 1:
                continue

            a_tag = li_tag.find(name='a', class_='pic')
            url = ''.join([domain, a_tag.attrs['href']])  # 景区入口
            dt_tag = li_tag.find(name='dt')
            info_list = list()
            # 提取景区名字和所处地区
            for a_tag_info in dt_tag.find_all(name='a'):
                title = a_tag_info.text
                title = re.sub('\s', '', title)
                info_list.append(title)
            info_list.reverse()
            attractions_info = ''.join(info_list)  # 景区信息如：广州广州塔
            yield AttractionInfo(url, attractions_info)

    def show_vacations_list(self, vacations_list):
        pass

    def next_page(self):
        self.__page += 1
        return self.__get_vacations_list__()

    def before_page(self):
        self.__page -= 1
        return self.__get_vacations_list__()


# keyword = input("搜索城市/景点/游记/问答/住宿/用户\n")
# keyword = '广州'
# a = AttractionListView()
# for i in a.get_vacations_url_entrance(keyword):
#     print(i)
# for i in a.next_page_list():
#     print(i)
# print("搜索结果：\n")
u = 'https://you.ctrip.com/sight/guangzhou152/107540.html'
g = CommentView()
for i in g.get_comment_detail(u):
    print(i)
for i in g.next_page():
    print(i)
for i in g.next_page():
    print(i)