from ape import accounts, project
from .utils.helper import MAX_UINT256, get_block, w3, get_timestamp

INITIAL_LIQUIDITY = w3.to_wei(1_000_000, "ether")
ADMIN_TOKENS = w3.to_wei(1_900_000, "ether")
BINANCE_TOKENS = w3.to_wei(9_000, "ether")


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
    usdc.mintPerUser([admin.address], [ADMIN_TOKENS], sender=admin)

    dai = project.Token.deploy("DAI", "DAI", sender=admin)
    dai.mintPerUser([admin.address], [ADMIN_TOKENS], sender=admin)

    bunny = project.Token.deploy("BUNNY", "BUNNY", sender=admin)
    bunny.mintPerUser([admin.address], [BINANCE_TOKENS], sender=admin)

    bnb = project.Token.deploy("BNB", "BNB", sender=admin)
    bnb.mintPerUser([admin.address], [BINANCE_TOKENS], sender=admin)

    # deploy uniswap contracts
    print("\n--- Deploying Uniswap Contracts ---\n")
    weth = project.WETH9.deploy(sender=admin)

    factory = project.UniswapV2Factory.deploy(admin.address, sender=admin)
    router = project.UniswapV2Router02.deploy(
        factory.address, weth.address, sender=admin
    )

    # creating pair and adding initial liquidity
    print("\n--- Creating Pairs and adding liquidity ---\n")
    usdc.approve(router.address, MAX_UINT256, sender=admin)
    dai.approve(router.address, MAX_UINT256, sender=admin)
    bunny.approve(router.address, MAX_UINT256, sender=admin)
    bnb.approve(router.address, MAX_UINT256, sender=admin)

    router.addLiquidity(  # creates USDC-DAI pair
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
    usdc_dai_pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, dai.address))

    router.addLiquidity(  # creates USDC-BNB pair
        usdc.address,
        bnb.address,
        w3.to_wei(900_000, "ether"),
        w3.to_wei(3_000, "ether"),
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    usdc_bnb_pair = project.UniswapV2Pair.at(factory.getPair(usdc.address, bnb.address))

    router.addLiquidity(  # creates DAI-BNB pair
        dai.address,
        bnb.address,
        w3.to_wei(900_000, "ether"),
        w3.to_wei(3_000, "ether"),
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    dai_bnb_pair = project.UniswapV2Pair.at(factory.getPair(dai.address, bnb.address))

    router.addLiquidity(  # creates BUNNY-BNB pair
        bunny.address,
        bnb.address,
        w3.to_wei(9_000, "ether"),  # 3x bunny per 1 bnb
        w3.to_wei(3_000, "ether"),
        0,
        0,
        admin.address,
        get_timestamp() * 2,
        sender=admin,
    )
    bunny_bnb_pair = project.UniswapV2Pair.at(
        factory.getPair(bunny.address, bnb.address)
    )

    # Deploying core contracts
    print("\n--- Deploying Core Contracts ---\n")
    zap_bsc = project.ZapBSC.deploy(
        router.address,
        bnb.address,
        usdc.address,
        bunny.address,
        sender=admin,
    )
    bunny_minter = project.BunnyMinter.deploy(
        zap_bsc.address,
        router.address,
        bnb.address,
        bunny.address,
        bunny_bnb_pair.address,
        sender=admin,
    )
    vault = project.AutoCompoundVault.deploy(
        usdc_bnb_pair.address,
        bunny_minter.address,
        sender=admin,
    )

    # --required updates to contract state
    print("\n--- Updating contract state ---\n")
    zap_bsc.setMinter(bunny_minter.address, sender=admin)
    bunny_minter.setMinter(vault.address, sender=admin)
    bunny.transferOwnership(
        bunny_minter.address, sender=admin
    )  # bunnyMinter given mint rights

    start_block = get_block()

    # define initial balance for attacker
    attacker_initial_bal = bnb.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker stole at least 1100 BNB in 2 blocks ---\n")

    # define ending balance for attacker
    attacker_ending_bal = bnb.balanceOf(attacker.address) / 10**18

    print(f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n---\n")

    # attacker steals at least 1100 BNB - only allowed 2 blocks to run exploit
    assert bnb.balanceOf(attacker.address) >= w3.to_wei(1_100, "ether")
    assert get_block() <= start_block + 2

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
