# coding: utf-8

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import io
import numpy as np
import boto3
import operator
import time
from datetime import datetime
from decimal import *

import json
from boto3.dynamodb.conditions import Key, Attr

s3 = boto3.client('s3')
dyn = boto3.resource('dynamodb', region_name='eu-central-1')
table = dyn.Table('nehody')

cfront = boto3.client('cloudfront')
cf_dist = 'E3ABKG4QXPTL3P'

def make_share(context, env):
    resp = table.query(
        KeyConditionExpression=Key('primkey').eq(1) & Key('tstamp').between(Decimal(time.time() - (86400 * 4)), Decimal(time.time()))
    )
    cr = {}
    kraje = resp['Items'][-1]['data']
    stamp = resp['Items'][-1]['tstamp']
    stamp = datetime.utcfromtimestamp(stamp).strftime('%d-%m-%Y').split('-')
    for kraj in kraje.values():
        for key in kraj:
            if key not in cr:
                cr[key] = 0
            cr[key] += kraj[key]
    
    # pro twitter
    pattern = Image.open('./imgs/canvas_tw.jpg', 'r').convert('RGBA')
    size = width, height = pattern.size
    draw = ImageDraw.Draw(pattern,'RGBA')
    font = ImageFont.truetype('Arial.ttf', 33)

    draw.text((105, 42), u'Statistiky dopravních nehod ' + str(int(stamp[0])) + '. ' + str(int(stamp[1])) + '. ' + stamp[2], font=font, fill='black')
    
    draw.text((277, 167), str(cr['M']), font=font, fill='black') # mrtví
    draw.text((421, 167), str(cr['TR']), font=font, fill='black') # těžce zranění
    draw.text((565, 167), str(cr['LR']), font=font, fill='black') # lehce zranění
    
    draw.text((277, 300), str(cr['PVA']), font=font, fill='black') # alkohol
    draw.text((421, 300), str(cr['NPJ']), font=font, fill='black') # přednost
    draw.text((565, 300), str(cr['NP']), font=font, fill='black') # nesprávné předjíždění
    draw.text((709, 300), str(cr['NR']), font=font, fill='black') # nepřiměřená rychlost
    
    draw.text((423, 376), str(round(cr[u'Š']/1000, 2)) + u' mil. Kč', font=font, fill='black')
    
    font = ImageFont.truetype('Arial.ttf', 52)
    draw.text((98, 229), str(cr['PN']), font=font, fill='black') # nehody celkem
    
    #zapsat obrazek
    out_img = io.BytesIO()
    pattern.save(out_img, format='PNG')

    putFile = s3.put_object(Bucket='datarozhlas', 
                            Key='nehody-pocitadlo/tw.png',
                            Body=out_img.getvalue(), 
                            ACL='public-read', 
                            ContentType='image/png')
    # pro fb, srát na to
    pattern = Image.open('./imgs/canvas_fb.jpg', 'r').convert('RGBA')
    size = width, height = pattern.size
    draw = ImageDraw.Draw(pattern,'RGBA')
    font = ImageFont.truetype('Arial.ttf', 33)

    draw.text((300, 70), u'Statistiky dopravních nehod ' + str(int(stamp[0])) + '. ' + str(int(stamp[1])) + '. ' + stamp[2], font=font, fill='black')
    
    draw.text((345, 244), str(cr['M']), font=font, fill='black') # mrtví
    draw.text((555, 244), str(cr['TR']), font=font, fill='black') # těžce zranění
    draw.text((757, 244), str(cr['LR']), font=font, fill='black') # lehce zranění
    
    draw.text((345, 427), str(cr['PVA']), font=font, fill='black') # alkohol
    draw.text((555, 427), str(cr['NPJ']), font=font, fill='black') # přednost
    draw.text((757, 427), str(cr['NP']), font=font, fill='black') # nesprávné předjíždění
    draw.text((958, 427), str(cr['NR']), font=font, fill='black') # nepřiměřená rychlost
    
    draw.text((555, 531), str(round(cr[u'Š']/1000, 2)) + u' mil. Kč', font=font, fill='black')
    
    font = ImageFont.truetype('Arial.ttf', 52)
    draw.text((105, 330), str(cr['PN']), font=font, fill='black') # nehody celkem
    
    #zapsat obrazek
    out_img = io.BytesIO()
    pattern.save(out_img, format='PNG')

    putFile = s3.put_object(Bucket='datarozhlas', 
                            Key='nehody-pocitadlo/fb.png',
                            Body=out_img.getvalue(), 
                            ACL='public-read', 
                            ContentType='image/png')

    #invalidace cache
    cfront.create_invalidation(DistributionId=cf_dist, InvalidationBatch={
        'Paths': {
            'Quantity': 2,
            'Items': ['/nehody-pocitadlo/tw.png', '/nehody-pocitadlo/fb.png']
        },
    'CallerReference': str(time.time())
    })
    return 'cajk'
