#coding:utf-8
import multiprocessing,threading
from bs4 import BeautifulSoup
import re
import os
import time
import requests

# 通过目录页获得该小说的所有章节链接后下载这本书
def thread_getOneBook(indexUrl):
    soup = get_pages(indexUrl)
    # 获取书名
    title = soup.select('div.readerListHeader:nth-child(4) > h1:nth-child(1)')[0].text[:-4]
    # 根据书名创建文件夹
    novel_name_path = r'D:\文件包\小说\%s' % (title)
    if not os.path.exists(novel_name_path):
        os.makedirs(novel_name_path)
        print(title, "小说文件夹创建成功———————————————————")
    # 加载此进程开始的时间
    print('下载 %s 的PID：%s...' % (title, os.getpid()))
    start = time.time()
    # 获取这本书的所有章节
    charts_url = []
    #章节有许多div组成，循环提取
    try:
        for i in range(100):
            charts = soup.find_all('div',attrs={'data-id':'%d'%(i)})[0]
            soups=BeautifulSoup(str(charts),'html.parser')
            tag=soups.find_all('a')
            for a in tag:
                url=re.search(r'href="(.*?)"',str(a)).group(1)
                charts_url.append(indexUrl + url) #章节链接
    except Exception as e:
        pass
    # 创建下载这本书进程
    p = multiprocessing.Pool()
    # 自己在下载的文件前加上编号，防止有的文章有上，中，下三卷导致有3个第一章
    num = 1
    for i in charts_url:
        p.apply_async(get_ChartTxt, args=(i, num,novel_name_path))
        # get_ChartTxt(i,title,num)
        num += 1

    print('等待 %s 所有的章节被加载......' % (title))
    p.close()
    p.join()
    end = time.time()
    print('下载 %s  完成，运行时间  %0.2f s.' % (title, (end - start)))
    print('开始生成 %s ................' % title)
    sort_allCharts(novel_name_path, "%s.txt" % title)
    # return
#解析请求网址
def get_pages(url):
    try:
        #创建日志文件夹
        if not os.path.exists(r'D:\文件包\小说\Log'):
            os.makedirs(r'D:\文件包\小说\Log')
        #请求章节目录
        data=requests.get(url)
        data.encoding="utf-8"
        #soup转换
        soup=BeautifulSoup(data.text,'html.parser')
        return soup
    except Exception as e:
        print(url+" 请求错误,原因："+e)
        with open(r'D:\文件包\小说\Log\req_error.txt','a',encoding='utf-8') as f:
            f.write(url+" 请求错误,原因："+e)
# 通过章节的url下载内容
def get_ChartTxt(url,num,txtpath):
    soup=get_pages(url)
    # 获取章节名
    subtitle = soup.select('.readerTitle > h1')[0].text
    # 判断是否有感言
    if re.search(r'.*?章', subtitle) is None:
        return
    print(subtitle, '开始下载....')
   #写入章节目录
    with open(r'%s\%s %s.txt' % (txtpath, num, subtitle), 'w', encoding='utf-8') as file:
        file.write('\t\t'+subtitle+'\n\n')
    # 获取章节文本
    try:
        #内容有许多不同的<P>标签组成
        for i in range(11):
            content = soup.find_all('p',attrs={'data-id':'%d'%(i)})[0].text.strip()
            # 按照指定格式替换章节内容，运用正则表达式
            content = re.sub(r'\s+', '\n\n\t', content)
            with open(r'%s\%s %s.txt' % (txtpath, num, subtitle), 'a', encoding='utf-8') as file:
                file.writelines('\t'+content)
    except Exception as e:
        pass
# 创建下载多本书书的进程
def process_getAllBook():
    # 输入你要下载的书的首页地址
    print('主程序的PID：%s' % os.getpid())
    book_indexUrl=[
        'http://www.22pq.com/book/232/232361/',
        'http://www.22pq.com/book/233/233516/',
        'http://www.22pq.com/book/233/233513/'
    ]
    print("-------------------开始下载-------------------")
    p = []
    for i in book_indexUrl:
        p.append(multiprocessing.Process(target=thread_getOneBook, args=(i,)))
    print("等待所有的主进程加载完成........")
    for i in p:
        i.start()
    for i in p:
        i.join()
    print("-------------------全部下载完成-------------------")
    return
#合成一本书
def sort_allCharts(path,filename):
    # 删除旧的书
    if os.path.exists(path+'\\'+filename):
        os.remove(path+'\\'+filename)
        print('旧的 %s 已经被删除' % filename)
    lists=os.listdir(path)
    # 对文件排序
    lists.sort(key=lambda i:int(re.match(r'(\d+)',i).group()))
    # 创建新书
    with open(r'%s\%s'%(path,filename),'a',encoding='utf-8') as f:
        for i in lists:
            with open(r'%s\%s' % (path, i), 'r', encoding='utf-8') as temp:
                f.writelines(temp.readlines())
            f.write('\n\n\n')
    print('新的 %s 已经被创建在当前目录 %s '%(filename,path))
    return
#根据小说
def search_novel():
    name=input('请输入小说名字：')
    url='http://www.22pq.com/modules/article/search.php'
    parms={'searchtype':'articlename','searchkey':name}
    #查询小说
    try:
        res=requests.post(url,data=parms)
        res.encoding="utf-8"
        soup=BeautifulSoup(res.text,'html.parser')
        content=soup.select('html body div.webBody div.webMain div#content div.listIndexUpdata ul.info h2 b a')
        print('搜索结果：')
        if content== []:
            print('小说不存在')
            return
        #创建搜索结果字段
        dict={}
        n=1
        for novel in content:
            name_url=novel.attrs['href']
            num=re.search(r'read/(.*?)\.html',name_url).group(1)[:-3]
            name_url=re.sub(r'\.html','/',name_url)
            name_url=re.sub(r'read','book/%s'%(num),name_url)
            dict[str(n)]=name_url
            print(n,novel.text)
            n+=1
        try:
            num=input('输入小说编号，选择下载的小说：')
            thread_getOneBook(dict[num])
        except:
            print('输入有误')
    except:
        print('请求失败')

if __name__ == '__main__':
    # thread_getOneBook('http://www.22pq.com/book/203/203713/') #活人禁忌
    # thread_getOneBook('http://www.22pq.com/book/233/233513/')
    # sort_allCharts('D:\文件包\小说\活人禁忌','活人禁忌.txt')
    # process_getAllBook()
    search_novel()