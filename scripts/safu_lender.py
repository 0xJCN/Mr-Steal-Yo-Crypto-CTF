from ape import accounts, project
from .utils.helper import MAX_UINT256, w3, get_timestamp, deploy_1820

ADMIN_USDC_TOKENS = w3.to_wei(2_000_000, "ether")
ADMIN_WBTC_TOKENS = w3.to_wei(2_000, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Attacker: {attacker}\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n---\n"
    )

    # deploying ERC1820Registry contract at 0x1820a4B7618BdE71Dce8cdc73aAB6C95905faD24
    print("\n--- Deploying ERC1820 Registry ---\n")
    deploy_1820()

    # deploy token contracts
    print("\n--- Deploying Token Contracts ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser([admin.address], [ADMIN_USDC_TOKENS], sender=admin)

    wbtc = project.Token777.deploy("wBTC", "wBTC", [], sender=admin)
    wbtc.mintPerUser(
        [admin.address, admin_user.address],
        [ADMIN_WBTC_TOKENS, w3.to_wei(1_000, "ether")],
        sender=admin,
    )
    # deploy uniswap contracts
    print("\n--- Deploying Uniswap Contracts ---\n")
    weth = project.WETH9.deploy(sender=admin)
    factory = project.UniswapV2Factory.deploy(admin.address, sender=admin)
    router = project.UniswapV2Router02.deploy(
        factory.address, weth.address, sender=admin
    )

    # creating pair and adding initial liquidity
    print("\n--- Creating Pair and adding liquidity ---\n")
    usdc.approve(router.address, MAX_UINT256, sender=admin)
    wbtc.approve(router.address, MAX_UINT256, sender=admin)

    router.addLiquidity(  # creates pair USDC-wBTC pair
        usdc.address,
        wbtc.address,
        ADMIN_USDC_TOKENS,
        ADMIN_WBTC_TOKENS,
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, wbtc.address))

    # deploy core contracts
    print("\n--- Deploying Core Contracts ---\n")
    money_market = project.MoneyMarket.deploy(sender=admin)
    money_market._supportMarket(wbtc.address, sender=admin)

    wbtc.approve(money_market.address, MAX_UINT256, sender=admin_user)
    money_market.supply(wbtc.address, w3.to_wei(1_000, "ether"), sender=admin_user)

    # define initial balance for attacker and money market
    attacker_initial_bal = wbtc.balanceOf(attacker.address) / 10**18
    market_initial_bal = wbtc.balanceOf(money_market.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_initial_bal}\n⇒ Market: {market_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker drained ~99% of WBTC from the market ---\n")

    # define ending balance for attacker and money market
    attacker_ending_bal = wbtc.balanceOf(attacker.address) / 10**18
    market_ending_bal = wbtc.balanceOf(money_market.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n⇒ Market: {market_ending_bal}\n---\n"
    )

    # attacker drains at least 99% of the wBTC from MoneyMarket
    assert wbtc.balanceOf(attacker.address) >= w3.to_wei(990, "ether")
    assert wbtc.balanceOf(money_market.address) <= w3.to_wei(10, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
