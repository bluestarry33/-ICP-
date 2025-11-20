import urllib.parse
import urllib3
import csv
import time
import json

# 禁用SSL警告（如果遇到证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def query_icp_info(domain, appcode):
    """
    查询单个域名的备案信息
    """
    host = 'https://lhappbass.market.alicloudapi.com'
    path = '/app/licence/query'
    url = host + path
    
    http = urllib3.PoolManager()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Authorization': 'APPCODE ' + appcode
    }
    
    bodys = {
        'keyword': domain,
        'page': '1'
    }
    
    try:
        post_data = urllib.parse.urlencode(bodys).encode('utf-8')
        response = http.request('POST', url, body=post_data, headers=headers)
        content = response.data.decode('utf-8')
        
        if content:
            return json.loads(content)
        else:
            return {'success': False, 'code': 999, 'msg': '空响应'}
            
    except json.JSONDecodeError as e:
        return {'success': False, 'code': 999, 'msg': f'JSON解析错误: {str(e)}'}
    except Exception as e:
        return {'success': False, 'code': 999, 'msg': f'请求异常: {str(e)}'}

def parse_icp_result(result, domain):
    """
    解析API返回的备案信息
    """
    # 检查请求是否成功
    if not result.get('success', False):
        code = result.get('code', 999)
        msg = result.get('msg', '未知错误')
        
        if code == 201:  # 查无数据
            return {
                '域名': domain,
                '主体备案号': '未备案',
                '服务备案号': '未备案',
                '主办单位': '未备案',
                '单位性质': '未备案',
                '服务名称': '未备案',
                '审核时间': 'N/A',
                '备案地址': 'N/A',
                '负责人': 'N/A',
                '查询状态': '未备案'
            }
        else:
            return {
                '域名': domain,
                '主体备案号': f'查询失败({code})',
                '服务备案号': f'查询失败({code})',
                '主办单位': f'查询失败({code})',
                '单位性质': f'查询失败({code})',
                '服务名称': f'查询失败({code})',
                '审核时间': 'N/A',
                '备案地址': 'N/A',
                '负责人': 'N/A',
                '查询状态': f'失败: {msg}'
            }
    
    # 成功响应，解析数据
    data = result.get('data', {})
    if not data or 'list' not in data or not data['list']:
        return {
            '域名': domain,
            '主体备案号': '无备案数据',
            '服务备案号': '无备案数据',
            '主办单位': '无备案数据',
            '单位性质': '无备案数据',
            '服务名称': '无备案数据',
            '审核时间': 'N/A',
            '备案地址': 'N/A',
            '负责人': 'N/A',
            '查询状态': '无数据'
        }
    
    # 获取第一条备案信息（通常是最新的）
    icp_info = data['list'][0]
    
    return {
        '域名': domain,
        '主体备案号': icp_info.get('mainLicence', 'N/A'),
        '服务备案号': icp_info.get('serviceLicence', 'N/A'),
        '主办单位': icp_info.get('unitName', 'N/A'),
        '单位性质': icp_info.get('natureName', 'N/A'),
        '服务名称': icp_info.get('serviceName', 'N/A'),
        '审核时间': icp_info.get('verifyTime', 'N/A'),
        '备案地址': icp_info.get('mainUnitAddress', 'N/A'),
        '负责人': icp_info.get('leaderName', 'N/A'),
        '查询状态': '成功'
    }

def read_domains_from_file(filename):
    """
    从文件读取域名列表
    """
    domains = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                domain = line.strip()
                if domain and not domain.startswith('#'):  # 跳过空行和注释
                    # 清理域名，移除http://等前缀
                    if '://' in domain:
                        domain = domain.split('://', 1)[1]
                    # 移除路径部分
                    if '/' in domain:
                        domain = domain.split('/')[0]
                    domains.append(domain)
    except Exception as e:
        print(f"读取文件错误: {e}")
    return domains

def save_results_to_csv(results, filename):
    """
    将结果保存到CSV文件
    """
    if not results:
        print("无结果可保存")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                '域名', '主体备案号', '服务备案号', '主办单位', 
                '单位性质', '服务名称', '审核时间', '备案地址', 
                '负责人', '查询状态'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        return True
    except Exception as e:
        print(f"保存CSV文件错误: {e}")
        return False

def main():
    # 配置信息
    appcode = ''
    input_file = '1.txt'
    output_file = 'icp_results.csv'
    
    # 读取域名列表
    print("正在读取域名列表...")
    domains = read_domains_from_file(input_file)
    
    if not domains:
        print(f"错误：在文件 {input_file} 中未找到有效的域名")
        return
    
    print(f"找到 {len(domains)} 个待查询域名")
    print("开始批量查询备案信息...")
    print("-" * 80)
    
    # 准备结果存储
    results = []
    success_count = 0
    no_record_count = 0
    failed_count = 0
    
    # 批量查询
    for i, domain in enumerate(domains, 1):
        print(f"[{i:03d}/{len(domains):03d}] 正在查询: {domain}")
        
        # 查询备案信息
        raw_result = query_icp_info(domain, appcode)
        
        # 解析结果
        parsed_result = parse_icp_result(raw_result, domain)
        
        # 添加到结果列表
        results.append(parsed_result)
        
        # 统计和显示结果
        status = parsed_result['查询状态']
        if status == '成功':
            success_count += 1
            icp_no = parsed_result['主体备案号']
            company = parsed_result['主办单位']
            print(f"     状态: ✅ 成功 | 备案号: {icp_no} | 主办单位: {company}")
        elif status == '未备案':
            no_record_count += 1
            print(f"     状态: ❌ 未备案")
        else:
            failed_count += 1
            print(f"     状态: ⚠️  {status}")
        
        # 添加延迟，避免请求过快（根据API限制调整）
        time.sleep(0.3)
    
    print("-" * 80)
    print("批量查询完成！")
    
    # 保存结果
    if save_results_to_csv(results, output_file):
        print(f"结果已保存到: {output_file}")
    else:
        print("保存结果文件失败")
    
    # 统计信息
    print("\n查询统计:")
    print(f"  成功查询: {success_count}")
    print(f"  未备案: {no_record_count}")
    print(f"  查询失败: {failed_count}")
    print(f"  总计: {len(domains)}")

def debug_single_domain():
    """
    调试单个域名查询
    """
    appcode = '12514d1f63294edc98a532368fc1c0fe'
    test_domain = 'baidu.com'  # 替换为你要测试的域名
    
    print(f"调试查询: {test_domain}")
    print("=" * 60)
    
    raw_result = query_icp_info(test_domain, appcode)
    
    print("API原始响应:")
    print(json.dumps(raw_result, indent=2, ensure_ascii=False))
    print("=" * 60)
    
    parsed_result = parse_icp_result(raw_result, test_domain)
    print("解析后的结果:")
    for key, value in parsed_result.items():
        print(f"  {key}: {value}")

if __name__ == '__main__':
    # 如果要调试单个域名，取消下面的注释
    # debug_single_domain()
    
    # 运行批量查询
    main()
