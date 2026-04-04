from binance.client import Client

client = Client("rGtTxj7qOCuTsRxUV9yl0K9r6POzLjmrnkc4O0zCpPNFyNtaVfJSV4ZCVIqUFnrK", "WgsOu6Ky4yIQmaWmYMuK0mO9X4un4pzx8JADZmqYNwcZIeKoi724sgjwdd4WdToL")

ordens = client.get_my_trades(symbol="BTCUSDT", limit=10)

if not ordens:
    print("Nenhuma operação encontrada.")
else:
    print(f"{'Data':<22} {'Lado':<6} {'Qtd BTC':<12} {'Preço':<12} {'Total USDT'}")
    print("-" * 65)
    for o in ordens:
        from datetime import datetime
        data = datetime.fromtimestamp(o['time']/1000).strftime('%d/%m/%Y %H:%M:%S')
        lado = "COMPRA" if o['isBuyer'] else "VENDA"
        print(f"{data:<22} {lado:<6} {float(o['qty']):<12.6f} ${float(o['price']):<11.2f} ${float(o['quoteQty']):.2f}")