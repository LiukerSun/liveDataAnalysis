import re
import chardet

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def extract_sku_from_titles(file_path):
    """
    从商品标题中提取货号
    货号格式：纯数字或字母数字组合，如D896、2501、A22等
    """
    
    # 检测文件编码
    encoding = detect_encoding(file_path)
    print(f"检测到文件编码: {encoding}")
    
    # 读取文件
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            titles = f.readlines()
    except UnicodeDecodeError:
        # 如果检测的编码失败，尝试常见编码
        encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    titles = f.readlines()
                print(f"使用编码: {enc}")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("无法解码文件，请检查文件编码")
    
    # 定义正则表达式 - 匹配各种货号格式
    # 主要匹配"美区大牌奢品-"或"美区奢品大牌-"后面的货号
    sku_pattern = r'美区[^-]*-([A-Z]*\d+[A-Z#]*|\d+[A-Z#]*|[A-Z]+\d+)'
    
    results = []
    
    for i, title in enumerate(titles, 1):
        title = title.strip()
        if not title:
            continue
            
        # 使用正则表达式提取货号
        match = re.search(sku_pattern, title)
        
        if match:
            sku = match.group(1)
            # 清理货号（去除#等符号）
            sku_clean = re.sub(r'[#]', '', sku)
            # 过滤掉一些明显不是货号的匹配（如过长的）
            if len(sku_clean) <= 10 and sku_clean and sku_clean != 'SZ001':
                results.append({
                    '行号': i,
                    '货号': sku_clean,
                    '原始货号': sku,
                    '商品标题': title
                })
        else:
            # 如果主模式没匹配到，尝试其他可能的货号格式
            # 匹配独立的货号模式（如春夏潮牌轻奢短袖上衣-D822）
            alt_pattern = r'-([A-Z]\d+|\d+[A-Z]?|\d+)(?:[^A-Z\d]|$|#)'
            alt_match = re.search(alt_pattern, title)
            if alt_match:
                sku = alt_match.group(1)
                if len(sku) <= 10 and sku and sku != 'SZ001':
                    results.append({
                        '行号': i,
                        '货号': sku,
                        '原始货号': sku,
                        '商品标题': title
                    })
    
    return results

def main():
    # 处理文件
    file_path = 'sku_name.txt'
    
    try:
        results = extract_sku_from_titles(file_path)
        
        print(f"\n成功提取到 {len(results)} 个货号：\n")
        
        # 显示前20个结果作为示例
        for result in results[:20]:
            print(f"行{result['行号']:3d}: 货号[{result['货号']}] - {result['商品标题'][:60]}...")
        
        if len(results) > 20:
            print(f"\n... 还有 {len(results) - 20} 个结果")
        
        # 保存结果到文本文件
        if results:
            with open('extracted_skus.txt', 'w', encoding='utf-8') as f:
                f.write("行号\t货号\t商品标题\n")
                for result in results:
                    f.write(f"{result['行号']}\t{result['货号']}\t{result['商品标题']}\n")
                    
            print(f"\n✅ 所有结果已保存到 'extracted_skus.txt' 文件")
            
            # 统计货号类型
            print("\n📊 货号类型统计：")
            sku_types = {}
            for result in results:
                sku = result['货号']
                if sku.isdigit():
                    sku_type = '纯数字'
                elif re.match(r'^[A-Z]+\d+$', sku):
                    sku_type = '字母+数字'
                elif re.match(r'^\d+[A-Z]+$', sku):
                    sku_type = '数字+字母'
                else:
                    sku_type = '混合格式'
                
                sku_types[sku_type] = sku_types.get(sku_type, 0) + 1
            
            for sku_type, count in sku_types.items():
                print(f"  {sku_type}: {count} 个")
                
            # 显示所有唯一货号
            unique_skus = list(set([result['货号'] for result in results]))
            unique_skus.sort()
            print(f"\n📝 所有唯一货号 ({len(unique_skus)} 个):")
            for i, sku in enumerate(unique_skus):
                if i % 10 == 0:
                    print()
                print(f"{sku:8s}", end=" ")
            print()
                
        else:
            print("❌ 未找到任何货号")
            
    except FileNotFoundError:
        print(f"❌ 文件 '{file_path}' 不存在")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")

if __name__ == "__main__":
    main() 