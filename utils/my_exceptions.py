
class PricePolicyInvalid(Exception):
    """
    用于抛出价格策略不合法的错误
    """
    def __init__(self,msg):
        self.msg = msg
