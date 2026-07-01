SECTOR_MAP = {
    "VCB": "Ngân hàng", "BID": "Ngân hàng", "CTG": "Ngân hàng",
    "TCB": "Ngân hàng", "MBB": "Ngân hàng", "ACB": "Ngân hàng",
    "SSI": "Chứng khoán", "VND": "Chứng khoán", "HCM": "Chứng khoán", "VCI": "Chứng khoán",
    "VHM": "Bất động sản", "VIC": "Bất động sản", "KDH": "Bất động sản",
    "NLG": "Bất động sản", "DXG": "Bất động sản",
    "HPG": "Thép", "HSG": "Thép", "NKG": "Thép",
    "GAS": "Dầu khí", "PVD": "Dầu khí", "PVS": "Dầu khí",
    "MWG": "Bán lẻ", "FRT": "Bán lẻ", "PNJ": "Bán lẻ",
    "FPT": "Công nghệ", "GMD": "Cảng biển / logistics",
    "VHC": "Thủy sản", "ANV": "Thủy sản",
    "TNG": "Dệt may", "STK": "Dệt may",
    "VCG": "Đầu tư công / xây dựng", "HHV": "Đầu tư công / hạ tầng",
    "CII": "Đầu tư công / hạ tầng", "LCG": "Đầu tư công / xây dựng",
}


SECTOR_THEMES = {
    "Ngân hàng": ["lãi suất", "tín dụng", "nợ xấu", "tỷ giá"],
    "Chứng khoán": ["thanh khoản thị trường", "margin", "VN-Index"],
    "Bất động sản": ["trái phiếu", "lãi suất vay", "pháp lý dự án"],
    "Thép": ["giá thép", "đầu tư công", "bất động sản Trung Quốc"],
    "Dầu khí": ["giá dầu", "OPEC", "đầu tư thượng nguồn"],
    "Bán lẻ": ["sức mua", "lạm phát", "mùa cao điểm tiêu dùng"],
    "Công nghệ": ["AI", "xuất khẩu phần mềm", "tỷ giá"],
    "Cảng biển / logistics": ["cước vận tải", "xuất nhập khẩu"],
    "Thủy sản": ["xuất khẩu", "tỷ giá", "nhu cầu Mỹ và Trung Quốc"],
    "Dệt may": ["đơn hàng xuất khẩu", "tỷ giá", "tồn kho bán lẻ"],
    "Đầu tư công / xây dựng": ["giải ngân đầu tư công", "giá vật liệu"],
    "Đầu tư công / hạ tầng": ["giải ngân đầu tư công", "BOT", "lãi suất"],
}


def get_sector(symbol: str) -> str:
    return SECTOR_MAP.get(symbol.upper(), "Khác")
