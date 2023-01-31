from ape import accounts, project
from .utils.helper import MAX_UINT256, w3, get_timestamp

INITIAL_LIQUIDITY = w3.to_wei(1_000_000, "ether")
ADMIN_USER_TOKENS = w3.to_wei(200_000, "ether")


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

    # deploy token contracts
    print("\n--- Deploying Token Contracts ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser([admin.address], [INITIAL_LIQUIDITY], sender=admin)

    dai = project.Token.deploy("DAI", "DAI", sender=admin)
    dai.mintPerUser(
        [admin.address, admin_user.address],
        [INITIAL_LIQUIDITY, ADMIN_USER_TOKENS],
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
    dai.approve(router.address, MAX_UINT256, sender=admin)

    router.addLiquidity(  # creates pair
        usdc.address,
        dai.address,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY,
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, dai.address))

    # setting up core contracts
    print("\n--- Setting up Core Contracts ---\n")
    project.BancorBondingCurve.deploy(sender=admin)  # hardcoded in ContinuousToken

    # --base DAI <-> EMN bonding curve
    eminence_currency_base = project.EminenceCurrencyBase.deploy(
        "Eminence",
        "EMN",
        999000,
        dai.address,
        sender=admin,
    )
    # --secondary EMN <-> TOKEN bonding curve
    eminence_currency = project.EminenceCurrency.deploy(
        "eTOKEN",
        "TOKEN",
        500000,
        eminence_currency_base.address,
        sender=admin,
    )
    # interacting with core contracts
    dai.approve(eminence_currency_base.address, MAX_UINT256, sender=admin_user)
    eminence_currency_base.approve(
        eminence_currency.address, MAX_UINT256, sender=admin_user
    )
    # --swap all DAI to EMN, convert 1/2 EMN to TOKEN
    eminence_currency_base.buy(ADMIN_USER_TOKENS, 0, sender=admin_user)
    received_emn = eminence_currency_base.balanceOf(admin_user.address)
    eminence_currency.buy(received_emn // 2, 0, sender=admin_user)

    # define initial balance for attacker
    attacker_initial_bal = dai.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker is in possession of entire collection ---\n")

    # define ending balances for attacker
    attacker_ending_bal = dai.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n---\n")

    # attacker steals at least 50k in DAI
    assert dai.balanceOf(attacker.address) >= w3.to_wei(50_000, "ether")

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
