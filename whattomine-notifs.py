#!/usr/bin/env python

import collections
import os
import requests
import json
from urllib.request import urlopen

# Edit-------------
ethos_panel_url = 'http://cryqua.ethosdistro.com/'
config_hash_url = 'https://configmaker.com/?hash=771196cdc4feb677'
config_txt_url = 'https://configmaker.com/my/ScaryHotSoulfulMammoth.txt'
node_backend_url = 'http://server.cryptoquarry.net:8081/'
email_to = 'admin@cryptoquarry.net'
coin_switch_percent = 2
# -----------------

# If true, does not change config or kick off Ansible. Sends all email to lucas.
debug = False

if debug:
    email_to = 'lucas@cryptoquarry.net'
    node_backend_url = 'http://localhost:8081/'


# Returns response from a json url
def get_json(url):
    initial_request = url
    r = requests.get(initial_request)
    data = json.loads(r.text)
    # //dumps the json object into an element
    json_str = json.dumps(data)
    # //load the json to a string
    resp = json.loads(json_str)
    return resp


# Sends and email from CQ notifs that can contain html
def email_html(addr_to, subject, html):
    # Import smtplib to provide email functions
    import smtplib

    # Import the email modules
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Define SMTP email server details
    smtp_server = 'smtp.gmail.com'
    smtp_user = 'cryptoquarrynotifs@gmail.com'
    smtp_pass = os.getenv("GMAIL_PASS")

    # Construct email
    msg = MIMEMultipart('alternative')
    msg['To'] = addr_to
    msg['From'] = smtp_user
    msg['Subject'] = subject

    # Record the MIME types of both parts - text/plain and text/html.
    attatchHTML = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(attatchHTML)

    # Send the message via an SMTP server
    s = smtplib.SMTP(smtp_server, 587)
    s.ehlo()
    s.starttls()
    s.login(smtp_user, smtp_pass)
    s.sendmail(smtp_user, addr_to, msg.as_string())
    s.quit()
    print("Email sent to: " + email_to)


# Returns the .txt url from the hash url
def get_config_txt_url(url):
    try:
        from bs4 import BeautifulSoup
        usock = urlopen(url)
        data = usock.read()
        usock.close()
        soup = BeautifulSoup(data, 'html.parser')
        soup = soup.find('input', {"class": "form-control"})['value']
    except Exception as e:
        error = 'Error getting config text url from config hash url'
        print(error)
        email_html(email_to, error, str(e))
        return

    return soup


def main():
    # Main
    print("--Script Start--")
    if debug:
        print("Debug Enabled")

    # TODO pull in dynamically first two rig names, and possibly hashrate regardless of miner client
    # Get json data for current ethos panel data
    try:
        panel_json = get_json(ethos_panel_url + '?json=yes')

        if panel_json['rigs']['ae7771']["condition"] != 'unreachable':
            panel_pool = panel_json['rigs']['ae7771']["pool"]
            miner_client = panel_json['rigs']['ae7771']["miner"]
        else:  # In case K1 is down, using D1 as backup
            if panel_json['rigs']['3ff3f3']["condition"] != 'unreachable':
                panel_pool = panel_json['rigs']['3ff3f3']["pool"]
                miner_client = panel_json['rigs']['3ff3f3']["miner"]
            else:
                email_html(
                    email_to, 'Error - could not reach rig K1 or D1 to pull pool info', '')
                return

        panel_hashrate = panel_json['per_info'][miner_client]['hash']
        panel_gpus = panel_json['per_info'][miner_client]['per_alive_gpus']

    except Exception as e:
        error = 'Error pulling JSON data from ethos panel'
        print(error)
        email_html(email_to, error, str(e))
        return

    # Get what we're currently mining
    if (panel_pool == "us1.ethermine.org:4444") or (panel_pool == "us2.ethermine.org:4444"):
        panel_mining_coin = "ETH"
    elif (panel_pool == "us1-etc.ethermine.org:4444") or (panel_pool == "us2-etc.ethermine.org:4444"):
        panel_mining_coin = "ETC"
    # elif (panel_pool == "us-east.pirlpool.eu:8004") or (panel_pool == "lb.geo.pirlpool.eu:8004"):
    #     panel_mining_coin = "PIRL"
    # elif (panel_pool == "us-music.2miners.com:4040") or (panel_pool == "music.2miners.com:4040"):
    #     panel_mining_coin = "MUSIC"
    # elif (panel_pool == "lb.geo.ellapool.eu:8009") or (panel_pool == "lb.geo.ellapool.eu:8844"):
    #     panel_mining_coin = "ELLA"
    elif (panel_pool == "us.expmine.pro:9009") or (panel_pool == "eu.expmine.pro:9009"):
        panel_mining_coin = "EXP"
    # elif (panel_pool == "ubiq-us.maxhash.org:8008") or (panel_pool == "ubiq-eu.maxhash.org:8008"):
    #     panel_mining_coin = "UBQ"
    # elif (panel_pool == "") or (panel_pool == ""):
    #     panel_mining_coin = "XMR"
    # elif (panel_pool == "") or (panel_pool == ""):
    #     panel_mining_coin = "Nicehash-Ethash"
    # elif (panel_pool == "") or (panel_pool == ""):
    #     panel_mining_coin = "Nicehash-CNV7"
    # elif (panel_pool == "") or (panel_pool == ""):
    #     panel_mining_coin = "GRFT"
    else:
        panel_mining_coin = "N/A - Coin pool profile not setup"
        print(panel_mining_coin)
        email_html(email_to, panel_mining_coin, 'Program Exit. The coin currently being mined was not recognized. More specifcally, the pool URL. ')
        return

    # Create a custom json URL to pull most profitable coin data, based on current hashrate from panel
    try:
        whattomine_url_dynamic = "https://whattomine.com/coins.json?utf8=✓&adapt_q_280x=0&adapt_q_380=0&adapt_q_fury=0&adapt_q_470=0&adapt_q_480=3&adapt_q_570=79&adapt_q_580=430&adapt_q_vega56=0&adapt_q_vega64=0&adapt_q_750Ti=0&adapt_q_1050Ti=0&adapt_q_10606=0&adapt_q_1070=0&adapt_q_1070Ti=0&adapt_q_1080=0&adapt_q_1080Ti=1&eth=true&factor%5Beth_hr%5D=12986.0&factor%5Beth_p%5D=0.0&factor%5Bzh_hr%5D=0.0&factor%5Bzh_p%5D=0.0&factor%5Bphi_hr%5D=0.0&factor%5Bphi_p%5D=0.0&factor%5Bcnh_hr%5D=0.0&factor%5Bcnh_p%5D=0.0&cn7=true&factor%5Bcn7_hr%5D=0.0&factor%5Bcn7_p%5D=0.0&eq=true&factor%5Beq_hr%5D=0.0&factor%5Beq_p%5D=0.0&lre=true&factor%5Blrev2_hr%5D=0.0&factor%5Blrev2_p%5D=0.0&ns=true&factor%5Bns_hr%5D=0.0&factor%5Bns_p%5D=0.0&factor%5Btt10_hr%5D=0.0&factor%5Btt10_p%5D=0.0&factor%5Bx16r_hr%5D=0.0&factor%5Bx16r_p%5D=0.0&factor%5Bl2z_hr%5D=0.0&factor%5Bl2z_p%5D=0.0&factor%5Bphi2_hr%5D=0.0&factor%5Bphi2_p%5D=0.0&factor%5Bxn_hr%5D=0.0&factor%5Bxn_p%5D=0.0&factor%5Bhx_hr%5D=0.0&factor%5Bhx_p%5D=0.0&factor%5Bcost%5D=0.1&sort=Profitability3&volume=0&revenue=3d&factor%5Bexchanges%5D%5B%5D=&factor%5Bexchanges%5D%5B%5D=bittrex&factor%5Bexchanges%5D%5B%5D=cryptopia&factor%5Bexchanges%5D%5B%5D=poloniex&dataset=Main&commit=Calculate"
        whattomine_json = get_json(whattomine_url_dynamic)
    except Exception as e:
        error = 'Error pulling JSON data from whattomine.com'
        print(error)
        email_html(email_to, error, str(e))
        return

    # Get json data for current BTC USD price
    try:
        btc_price_json = get_json(
            "https://api.coindesk.com/v1/bpi/currentprice/btc.json")
        btc_price = btc_price_json['bpi']['USD']['rate_float']
    except Exception as e:
        error = 'Error pulling btc JSON data from coindesk.com, (not script breaking, continuing)'
        print(error)
        email_html(email_to, error, str(e))

    # Assign revenue values for each coin, from whattomine json data
    error = 'Error pulling JSON data from whattomine.com'
    json_field = 'btc_revenue24'
    try:
        eth_profit = whattomine_json['coins']['Ethereum'][json_field]
    except Exception as e:
        eth_profit = "0"
        print(error + ", " + str(e))
        #email_html(email_to, error, str(e))
    try:
        etc_profit = whattomine_json['coins']['EthereumClassic'][json_field]
    except Exception as e:
        etc_profit = "0"
        print(error + ", " + str(e))
        #email_html(email_to, error, str(e))
    # try:
    #     pirl_profit = whattomine_json['coins']['Pirl'][json_field]
    # except Exception as e:
    #     pirl_profit = "0"
    #     print(error + ", " + str(e))
    #     #email_html(email_to, error, str(e))
    # try:
    #     music_profit = whattomine_json['coins']['Musicoin'][json_field]
    # except Exception as e:
    #     music_profit = "0"
    #     print(error + ", " + str(e))
    #     #email_html(email_to, error, str(e))
    # try:
    #     ella_profit = whattomine_json['coins']['Ellaism'][json_field]
    # except Exception as e:
    #     ella_profit = "0"
    #     print(error + ", " + str(e))
    #     #email_html(email_to, error, str(e))
    try:
        exp_profit = whattomine_json['coins']['Expanse'][json_field]
    except Exception as e:
        exp_profit = "0"
        print(error + ", " + str(e))
        #email_html(email_to, error, str(e))
    # try:
    #     ubq_profit = whattomine_json['coins']['Ubiq'][json_field]
    # except Exception as e:
    #     ubq_profit = "0"
    #     print(error + ", " + str(e))
    #     #email_html(email_to, error, str(e))

    # Build coin pairs
    coin_list = [
        ('ETH', eth_profit),
        ('ETC', etc_profit),
        # ('PIRL', pirl_profit),
        # ('MUSIC', music_profit),
        # ('ELLA', ella_profit),
        ('EXP', exp_profit),
        # ('UBQ', ubq_profit),
    ]

    # Sort coin pairs by profit number and store most profit coin values
    coin_list_sorted = sorted(
        coin_list, key=lambda coin: coin[1], reverse=True)[0]
    most_profit_coin = coin_list_sorted[0]
    most_profit_num = coin_list_sorted[1]

    # Find the current mining coin's profit out of the coin list, then store.
    try:
        temp = [item for item in coin_list if item[0] == panel_mining_coin]
        mining_coin_profit_num = temp[0][1]
    except Exception as e:
        error = 'Error finding the current mining coins profit'
        print(error)
        email_html(email_to, error, str(e))
        return

    # if debug:
    #     most_profit_num = 100

    # Gets the percent difference between 'most_profit_num' and 'mining_coin_profit_num'
    if float(most_profit_num) > float(mining_coin_profit_num):
        change_percent = ((float(
            most_profit_num)-float(mining_coin_profit_num))/float(mining_coin_profit_num))*100
    else:
        change_percent = 0

    # Gets current coin override from node backend
    try:
        data = urlopen(node_backend_url+"which_coin")
        coin_override = ""
        for line in data:
            line = line.decode('utf-8')
            coin_override = line
    except Exception as e:
        coin_override = ""
        error = 'Error pulling coin override from node backend'
        print(error)
        #email_html(email_to, error, str(e))
        #return

    # Determine if coin override was requested
    is_coin_override = False
    if (coin_override == "Most Profitable"):
        is_coin_override = False
        print("Most Profitable requested from panel")
    elif (coin_override == ""):
        is_coin_override = False
        print("Could not reach coin override from backend, defualting to Most Profitable")
    else:
        is_coin_override = True
        if coin_override == "Ethereum (ETH)":
            coin_override = "ETH"
        elif coin_override == "Ether Classic (ETC)":
            coin_override = "ETC"
        # elif coin_override == "Pirl (PIRL)":
        #     coin_override = "PIRL"
        # elif coin_override == "Musicoin (MUSIC)":
        #     coin_override = "MUSIC"
        # elif coin_override == "Ellaism (ELLA)":
        #     coin_override = "ELLA"
        elif coin_override == "Expanse (EXP)":
            coin_override = "EXP"
        # elif coin_override == "Ubiq (UBQ)":
        #     coin_override = "UBQ"

    if panel_mining_coin == coin_override:
        print("Rigs are already mining requested override coin")
        return

    print("Currently mining: " + panel_mining_coin)

    # Gets last ip from node backend
    try:
        data = urlopen(node_backend_url+"last_ip")
        last_ip = ""
        for line in data:
            line = line.decode('utf-8')
            last_ip = line
    except Exception as e:
        last_ip = "Unknown"
        error = 'Error pulling last ip from node backend'
        print(error)
        #email_html(email_to, error, str(e))

    if (is_coin_override):
        print("Coin Override ENABLED. Switching to: "+coin_override)
        most_profit_coin = coin_override
        email_html(
            email_to, "Panel Override Was Used - Switching to Coin: "+coin_override, '<p>Triggered by IP: '+str(last_ip[7:])+'</p><div><div>-Sent from whattomine-notifs.py</div></div>')

    elif change_percent >= coin_switch_percent and not is_coin_override:
        print("Most profitable: " + most_profit_coin)
        print("Change percent: " + format(change_percent, '.2f') + '%')
        print(most_profit_coin+" has a "+str(coin_switch_percent)+"% or better profits than current (" +
              format(change_percent, '.2f')+"%)")
        print("**SWITCHING COINS**")

        email_body_html = "<h3>Panel Info</h3><table><tbody><tr><td><strong>Hashrate</strong></td><td><div><div>" + str(
            panel_hashrate) + "</div></div></td></tr><tr><td><strong>GPUs</strong></td><td><div><div>" + str(
            panel_gpus) + "</div></div></td></tr><tr><td><strong>Mining</strong></td><td><div><div>" + panel_mining_coin + "</div></div></td></tr></tbody></table><p>-Sent from whattomine-notifs.py</p>"
        if not debug:
            email_html(email_to, 'New Most Profitable Coin Found - Switching to: ' + most_profit_coin,
                       most_profit_coin+" has a "+str(coin_switch_percent)+"% or better profits than current (" + format(change_percent, '.2f')+"%)\n\n" + email_body_html)
        else:
            email_html(email_to, '[DEBUG MODE] New Most Profitable Coin Found - Switching to: ' + most_profit_coin,
                       most_profit_coin+" has a "+str(coin_switch_percent)+"% or better profits than current (" + format(change_percent, '.2f')+"%)\n\n" + email_body_html)
    else:
        print("Most profitable: " + most_profit_coin)
        print("Change percent: " + format(change_percent, '.2f') + '%')
        print("We are currently mining most profitable coin, or next most profitable coin is less than "+str(coin_switch_percent)+"% better")
        return

    # GET request to pull in current config data
    # config_data = urlopen(get_config_txt_url(
    #     config_hash_url)).read().decode('utf-8')
    config_data = urlopen(config_txt_url).read().decode('utf-8')

    # Un-comments most profitable coin text block, and comments previously mining text block
    config_data_new = ''
    found_new = False
    found_old = False
    for line in config_data.splitlines():
        if '#BEGIN ' + most_profit_coin in line:
            found_new = True
            config_data_new += line + '\n'
            continue
        if found_new:
            if '#END ' + most_profit_coin in line:
                found_new = False
            else:
                line = line.replace("#", "")
        if '#BEGIN ' + panel_mining_coin in line:
            found_old = True
            config_data_new += line + '\n'
            continue
        if found_old:
            if '#END ' + panel_mining_coin in line:
                found_old = False
            else:
                if line[:1] != '#':
                    line = '#' + line
        config_data_new += line + '\n'

    # Encoding
    config_data = collections.OrderedDict()
    config_data['Submit'] = 'Save Changes'
    config_data['hash'] = config_hash_url.split("hash=", 1)[1]
    config_data['update'] = config_data_new

    if not debug:
        # Update existing config file to mine the new coin
        r = requests.post(
            url='https://configmaker.com/index.php',
            data=config_data,
            headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                     'Accept-Encoding': 'gzip, deflate, br',
                     'Referer': config_hash_url,
                     'Cache-Control': 'max-age=0',
                     'Origin': 'https://configmaker.com',
                     'Upgrade-Insecure-Requests': '1'})
        # print(r.status_code)
        # print(r.raise_for_status())
        # print(r.headers)
        # print(r.text)

        # Kick off Ansible to pull the new config and reboot rigs
        gitlab_build_token = os.getenv("ANSIBLE_BUILD_TOKEN")
        if gitlab_build_token is None:
            print(
                "Unable to get gitlab_build_token out of env vars, failed to kick off ansible...")
            return
        else:
            print("Using gitlab_build_token: " + gitlab_build_token)

        data_obj = {'token': gitlab_build_token, 'ref': 'master',
                    'variables[ANSIBLE_TASK]': 'pull-and-update-config.yaml'}
        r = requests.post(
            url='https://gitlab.com/api/v4/projects/5282532/trigger/pipeline',
            data=data_obj,
            headers={'Content-Type': 'multipart/form-data'}
        )


if __name__ == "__main__":
    main()
