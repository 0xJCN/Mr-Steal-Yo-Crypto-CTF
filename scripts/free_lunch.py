from ape import accounts, project
from .utils.helper import w3, get_timestamp

INITIAL_DEX_TOKENS = w3.to_wei(1000000, "ether")
INITIAL_ATTACKER_TOKENS = w3.to_wei(100, "ether")
SIMULATED_TRADING_AMOUNT = w3.to_wei(10000, "ether")
SUSHI_BAR = "0x" + "11" * 20


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Attacker: {attacker}\n---\n"
    )

    # deploy token contracts
    print("\n--- Deploying WETH ---\n")
    weth = project.WETH9.deploy(sender=admin)

    print("\n--- Deploying USDC ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    # mint USDC tokens for admin and attacker
    print(
        "\n-- Minting 1 million USDC tokens for the admin and 100 for the attacker --\n"
    )
    usdc.mintPerUser(
        [admin.address, attacker.address],
        [INITIAL_DEX_TOKENS, INITIAL_ATTACKER_TOKENS],
        sender=admin,
    )

    print("\n--- Deploying Safu Token ---\n")
    safu = project.Token.deploy("SAFU", "SAFU", sender=admin)
    # mint SAFU tokens for admin and attacker
    print(
        "\n-- Minting 1 million SAFU tokens for the admin and 100 for the attacker --\n"
    )
    safu.mintPerUser(
        [admin.address, attacker.address],
        [INITIAL_DEX_TOKENS, INITIAL_ATTACKER_TOKENS],
        sender=admin,
    )

    # deploy SafuSwap + SafuMaker contracts
    print("\n--- Deploying Safu Factory contract ---\n")
    factory = project.UniswapV2Factory.deploy(admin.address, sender=admin)

    print("\n--- Deploying Safu Factory contract ---\n")
    router = project.UniswapV2Router02.deploy(
        factory.address, weth.address, sender=admin
    )

    print("\n--- Deploying Safu Maker contract ---\n")
    maker = project.SafuMakerV2.deploy(
        factory.address, SUSHI_BAR, safu.address, usdc.address, sender=admin
    )
    # setFeeTo Maker contract
    print("\n--- Setting swap fee to Maker Contract ---\n")
    factory.setFeeTo(maker.address, sender=admin)

    # add initial liquidity
    print("\n--- Adding initial liquidity ---\n")
    usdc.approve(router.address, INITIAL_DEX_TOKENS, sender=admin)
    safu.approve(router.address, INITIAL_DEX_TOKENS, sender=admin)

    router.addLiquidity(  # creates pair
        usdc.address,
        safu.address,
        INITIAL_DEX_TOKENS,
        INITIAL_DEX_TOKENS,
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    # getting the USDC-SAFU trading pair
    print("\n--- Getting pair ---\n")
    pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, safu.address))

    # simulates trading activity, as LP is issued to feeTo address for trading rewards
    print("\n--- Simulating trading activity ---\n")
    pair.transfer(maker.address, SIMULATED_TRADING_AMOUNT, sender=admin)  # 1% of LP

    # define initial balances for attacker and dex
    attacker_safu_initial = safu.balanceOf(attacker.address) / 10**18
    attacker_usdc_initial = usdc.balanceOf(attacker.address) / 10**18

    dex_safu_initial = safu.balanceOf(pair.address) / 10**18
    dex_usdc_initial = usdc.balanceOf(pair.address) / 10**18

    print(
        f"\n--- \nDEX Initial Balances:\n⇒ SAFU: {dex_safu_initial}\n⇒ USDC: {dex_usdc_initial}\n---\n"
    )
    print(
        f"\n--- \nAttacker Initial Balances:\n⇒ SAFU: {attacker_safu_initial}\n⇒ USDC: {attacker_usdc_initial}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker has increased SAFU+USDC funds by at least 50x ---\n"
    )

    # define ending balances for attacker and dex
    attacker_safu_ending = safu.balanceOf(attacker.address) / 10**18
    attacker_usdc_ending = usdc.balanceOf(attacker.address) / 10**18

    dex_safu_ending = safu.balanceOf(pair.address) / 10**18
    dex_usdc_ending = usdc.balanceOf(pair.address) / 10**18

    print(
        f"\n--- \nDEX Ending Balances:\n⇒ SAFU: {dex_safu_ending}\n⇒ USDC: {dex_usdc_ending}\n---\n"
    )
    print(
        f"\n--- \nAttacker Ending Balances:\n⇒ SAFU: {attacker_safu_ending}\n⇒ USDC: {attacker_usdc_ending}\n---\n"
    )

    assert usdc.balanceOf(attacker.address) / 10**18 >= 100 * 50
    assert safu.balanceOf(attacker.address) / 10**18 >= 100 * 50

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
