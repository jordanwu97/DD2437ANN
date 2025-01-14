from util import *
from rbm import RestrictedBoltzmannMachine
from dbn import DeepBeliefNet
import pickle
import matplotlib.pyplot as plt

if __name__ == "__main__":
    
    image_size = [28, 28]
    train_imgs, train_lbls, test_imgs, test_lbls = read_mnist(
        dim=image_size, n_train=60000, n_test=10000
    )

    try:
        dbn: DeepBeliefNet = pickle.load(open("savefiles/dbn_greedy.pkl", "rb"))
    
    except IOError:
        dbn = DeepBeliefNet(
                sizes={
                    "vis": image_size[0] * image_size[1],
                    "hid": 500,
                    "pen": 500,
                    "top": 2000,
                    "lbl": 10,
                },
                image_size=image_size,
                n_labels=10,
                batch_size=200,
            )    

        """ greedy layer-wise training """

        dbn.train_greedylayerwise(
            vis_trainset=train_imgs, lbl_trainset=train_lbls, n_iterations=10
        )

        pickle.dump(dbn, open("savefiles/dbn_greedy.pkl", "wb"))

    #dbn.recognize(train_imgs[:100], train_lbls[:100])

    #for name, rbm in dbn.rbm_stack.items():
    #    plt.plot(range(len(rbm.recon_losses)), rbm.recon_losses, label=f"{name}")
    #    plt.annotate(f"{rbm.recon_losses[-1]:.5f}", (len(rbm.recon_losses) - 1,rbm.recon_losses[-1]))

    #plt.xlim(-0.5, len(rbm.recon_losses) + 0.5)
    #plt.title("Layers Recon Loss")
    #plt.ylabel("Reconstruction Loss")
    #plt.xlabel("# Epochs")
    #plt.legend()
    #plt.savefig("pictures/4_2_recon_losses.png")

    # for name, im, lb in [("train", train_imgs, train_lbls), ("test", test_imgs, test_lbls)]:
    #     acc = []
    #     for trials in range(10):
    #         acc.append(dbn.recognize(train_imgs, train_lbls))
    #         print (name, acc[-1])

    #     print (f"{name} & {np.mean(acc):.5f} & {np.std(acc):.5f}")

    ### DO IMAGE GEN HERE!

    labels = np.zeros([1,10])
    labels[0,0] = 1
    vis = dbn.generate(labels)
    vis = vis.reshape(28,28)
    plt.clf()
    plt.subplot(4,5,1)
    plt.imshow(vis)
    plt.show(block=False)
    plt.pause(0.1)
    for it in range(1,10):
        labels[0,it] = 1
        labels[0,it-1] = 0
        print(labels)
        vis = dbn.generate(labels)
        vis = vis.reshape(28,28)
        plt.subplot(4,5,it+1)
        plt.imshow(vis)
        plt.show(block=False)
        plt.pause(0.1)
    plt.savefig("pictures/4_2_generation.png")
    



