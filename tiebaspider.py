#coding:utf-8
import urllib2
import urllib
import re
from bs4 import BeautifulSoup
import os
import multiprocessing
from pybloom import BloomFilter
import socket
import time
import os

#set the socket timeout
timeout =10
socket.setdefaulttimeout(timeout)

def urlparse(url):
    """
    input an url,and return the parse result
    The result is organized by the beautifulsoup,and it's different from the original response from url.
    """
    request = urllib2.Request(url)
    try:
        response = urllib2.urlopen(request)
    except URLError as e:
        if hasattr(e,'readon'):
            print 'We failed to reach a server.'
            print 'Reason:',e.reason
        elif hasattr(e,'code'):
            print 'The server couldn\'t fullfill the request.'
            print 'Error code:', e.code
    soup = BeautifulSoup(response, 'html.parser')
    organized_html =  soup.prettify()
    return organized_html

def get_tieba_totalpage(organized_html):
    """
    using re module to get the total page of this tieba,directly return the total page.
    """
    lastpattern = re.compile(r'<a class="last pagination-item " href=.*?;pn=(.*?)">')  # 正则匹配寻找最后一页
    lastpage = re.findall(lastpattern,organized_html)
    pagecount = int(lastpage[0]) / 50
    print u"此贴吧共有  %d  页" %(pagecount+1)
    return pagecount+1

def get_tie_inside_page(organized_html):
    """
    all the ties of Baidu tieba are in this form:'tieba.baidu.com/p/number'
    This function is to use re module to get the '/p/number' in this page.
    """
    # 正则匹配<a class="j_th_tit " href="(address)" target="_blank" tittle=...>,获取贴吧每一页的子贴
    pattern = re.compile(
        r'<a class="j_th_tit.*?href="(.*?)".*?="_blank".*?>')
    address = re.findall(pattern, organized_html)
    return address

def get_all_tie_address(pagecount,original_url):
    '''
    according to the original url and the pagecount,this function is to 
    return all the tie page url addresses in this tieba.
    '''
    page = {}
    for i in range(pagecount):
        url =original_url+'&pn='+str(i*50)
        #print u'获取此页所有贴子地址'
        page[i] = url
    return page

def getallnumlist(url):
    """
    get all numlist like 'p/400000' in the tieba
    """
    parse = urlparse(url)
    totalpage = get_tieba_totalpage(parse)
    page = get_all_tie_address(totalpage,url)
    numlist = []
    for i in page.keys():
        pagehtml = {}
        pagehtml[i]=urlparse(page[i])
        numlist = numlist+(get_tie_inside_page(pagehtml[i]))
    return numlist


def getImg(tienumber):
    """
    get all the img url in the tie url ,and return a list
    """
    url = 'http://tieba.baidu.com'+tienumber
    html = urlparse(url)
    #reg = r'src="(.+?\.jpg" pic_ext'
    imgre = re.compile(r'src="(.+?\.jpg)" width=".+?"')
    imglist = re.findall(imgre,html)
    downloadIMG(imglist,tienumber[3:])
    
    #x=0
    #for imgurl in imglist:
        #urllib.urlretrieve(imgurl,'i_j_%s.jpg' %x)
        #x+=1

def downloadIMG(imglist,tienumber):
    """
    input the img url list and download all the imgs
    """
    for i,url in enumerate(imglist):
        print url,i
        urllib.urlretrieve(url,filename = '%s.jpg' %(tienumber+' '+str(i)))
    # f = codecs.open("demo.txt",'wb','utf-8')
    # f.write(b)
    # f.close()

def multiprocessdownload(numlist):
    """
    use multiprocess to download img
    """
    p = multiprocessing.Pool(processes =multiprocessing.cpu_count())
    time1 =time.time()
    for i in numlist:
        print i
        #getImg(i)
        download = p.apply_async(getImg ,args =(i,))
    p.close()
    p.join()

    time2 =time.time()
    print time2-time1


#def recordtext():
def record(url):
    """
    first time download tieba img
    create a bloomfliter for the next time downloading
    """
    numlist =getallnumlist(url)
 
    bloomfilter =BloomFilter(1000000)
    for number in numlist:
        bloomfilter.add(number)
    with open('./%s/check/bloomfilter' %(url[28:])  ,'ab+') as b:
        bloomfilter.tofile(b)
    #print 'pool'              
    
    multiprocessdownload(numlist)


def main():
    #url =raw_input('input the tieba you like')
    #the tieba url you want to download the img ,pay attention to the format,'/f?kw=XXXXXXXXX'
    url ='http://tieba.baidu.com/f?kw=轴心国画室'
    if not os.path.exists('%s'  %(url[28:])  ):
        os.makedirs('%s' %(url[28:])  )
        os.makedirs('./%s/check' %(url[28:])  )
        record(url)
    else:
        numlist =getallnumlist(url)        
        #ues the bloomfilter first time create and find the tie that haven't download
        with open('./%s/check/bloomfilter' %(url[28:]) ,'rb') as b:
            bloomfilter =BloomFilter.fromfile(b)
        img_no_download =[]
        for i in numlist:
            if not bloomfilter.add(i):
                img_no_download += i



        if not img_no_download:
            print 'nothing update'
        else:
            multiprocessdownload(img_no_download)
        #for i in a:
        #print i[0:-1]
    

if __name__ == '__main__':
    main()
