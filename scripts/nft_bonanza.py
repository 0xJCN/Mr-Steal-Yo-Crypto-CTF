from ape import accounts, project
from .utils.helper import w3

NFT_PRICE = w3.to_wei(100, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    admin = accounts.test_accounts[0]
    admin_user = accounts.test_accounts[1]
    attacker = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Attacker: {attacker}\n---\n"
    )

    # deploy payment tokens and NFT for marketplace
    print("\n--- Deploying payment token and NFT ---\n")
    usdc = project.Token.deploy("USDC", "USDC", sender=admin)
    usdc.mintPerUser([admin_user.address], [NFT_PRICE], sender=admin)

    nftA = project.Nft721.deploy("APES", "APES", sender=admin)
    nftB = project.Nft721.deploy("ApEs", "ApEs", sender=admin)

    # adminUser minted NFTs from collections A & B
    print("\n--- Admin User minting NFTs from collections A & B ---\n")
    nftA.mintForUser(admin_user.address, 1, sender=admin)
    nftB.mintForUser(admin_user.address, 1, sender=admin)

    # deploying the marketplace & setup
    print("\n--- Deploying and setting up Bonanza Marketplace ---\n")
    marketplace = project.BonanzaMarketplace.deploy(
        50,
        admin.address,
        usdc.address,
        sender=admin,
    )
    marketplace.addToWhitelist(nftA.address, sender=admin)
    marketplace.addToWhitelist(nftB.address, sender=admin)

    # adminUser lists NFTs on the bonanza marketplace
    print("\n--- Admin User lists NFTs on the Marketplace ---\n")
    nftA.setApprovalForAll(marketplace.address, True, sender=admin_user)
    nftB.setApprovalForAll(marketplace.address, True, sender=admin_user)

    marketplace.createListing(
        nftA.address,
        0,
        1,
        NFT_PRICE,
        0,
        sender=admin_user,
    )
    marketplace.createListing(
        nftB.address,
        0,
        1,
        NFT_PRICE,
        0,
        sender=admin_user,
    )
    assert nftA.balanceOf(admin_user.address) == 1
    assert nftB.balanceOf(admin_user.address) == 1

    # define initial balances for staking contract and attacker
    admin_user_initial_bal = nftA.balanceOf(admin_user.address) + nftB.balanceOf(
        admin_user.address
    )
    attacker_initial_bal = nftA.balanceOf(admin_user.address) + nftB.balanceOf(
        admin_user.address
    )

    print(
        f"\n--- \nInitial Balances:\n⇒ Rewards Advisor: {admin_user_initial_bal}\n⇒ Attacker: {attacker_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After expoit: attacker steals all listed NFTs from bonanza marketplace ---\n"
    )

    # define ending balances for staking contract and attacker
    admin_user_ending_bal = nftA.balanceOf(admin_user.address) + nftB.balanceOf(
        admin_user.address
    )
    attacker_ending_bal = nftA.balanceOf(admin_user.address) + nftB.balanceOf(
        admin_user.address
    )

    print(
        f"\n--- \nEnding Balances:\n⇒ Rewards Advisor: {admin_user_ending_bal}\n⇒ Attacker: {attacker_ending_bal}\n---\n"
    )
    assert nftA.balanceOf(admin_user.address) == 0
    assert nftB.balanceOf(admin_user.address) == 0
    assert nftA.balanceOf(attacker.address) == 1
    assert nftB.balanceOf(attacker.address) == 1

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
