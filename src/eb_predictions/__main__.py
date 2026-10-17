from __future__ import annotations
import os, json
import httpx

def main():
    client = httpx.Client(timeout=60, auth=(os.environ['WP_USERNAME'], os.environ['WP_APP_PASSWORD']), follow_redirects=True)
    r = client.get(os.environ.get('WP_BASE_URL','https://beteasy.ru').rstrip('/') + '/wp-json/wp/v2/prediction', params={'per_page':3,'orderby':'date','order':'desc'})
    for p in r.json():
        acf = p.get('acf') or {}
        print(p['id'], p['title']['rendered'])
        print('  match_datetime:', repr(acf.get('match_datetime')))
        print('  status:', acf.get('prediction_status'))

if __name__ == '__main__':
    main()
