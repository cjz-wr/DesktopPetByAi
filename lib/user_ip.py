import requests,geocoder

# g = geocoder.ip('me')
# print(g.ip)


# url = "https://tools.ucii.cn/tools/ip-lookup/api.php?ip=120.239.148.47"
# resp = requests.get(url)
# print(resp.json())


class UserIP:
    def __init__(self):
        pass

    def sendIp(self):
        g = geocoder.ip('me')
        return g.ip
    
    def sendAddressIp(self,ip):
        url = f"https://tools.ucii.cn/tools/ip-lookup/api.php?ip={ip}"
        resp = requests.get(url)
        return resp.json()
    

    def sendAllAddress(self):
        url = f"https://tools.ucii.cn/tools/ip-lookup/api.php?ip={self.sendIp()}"
        resp = requests.get(url)
        return resp.json()
    
    def sendAddress(self):
        url = f"https://tools.ucii.cn/tools/ip-lookup/api.php?ip={self.sendIp()}"
        resp = requests.get(url)
        return resp.json()['data']['detail']


def main():
    user_ip = UserIP()
    print(user_ip.sendIp())
    print(user_ip.sendAddressIp("120.239.148.47"))
    print(user_ip.sendAllAddress())
    print(user_ip.sendAddress())

if __name__ == "__main__":
    main()