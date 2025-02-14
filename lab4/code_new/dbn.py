from util import *
from rbm import RestrictedBoltzmannMachine


class DeepBeliefNet:

    """ 
    For more details : Hinton, Osindero, Teh (2006). A fast learning algorithm for deep belief nets. https://www.cs.toronto.edu/~hinton/absps/fastnc.pdf

    network          : [top] <---> [pen] ---> [hid] ---> [vis] 
                               `-> [lbl] 
    lbl : label
    top : top
    pen : penultimate
    hid : hidden
    vis : visible
    """

    def __init__(self, sizes, image_size, n_labels, batch_size):

        """
        Args:
          sizes: Dictionary of layer names and dimensions
          image_size: Image dimension of data
          n_labels: Number of label categories
          batch_size: Size of mini-batch
        """

        self.rbm_stack = {
            "vis--hid": RestrictedBoltzmannMachine(
                ndim_visible=sizes["vis"],
                ndim_hidden=sizes["hid"],
                is_bottom=True,
                image_size=image_size,
                batch_size=batch_size,
            ),
            "hid--pen": RestrictedBoltzmannMachine(
                ndim_visible=sizes["hid"],
                ndim_hidden=sizes["pen"],
                batch_size=batch_size,
            ),
            "pen+lbl--top": RestrictedBoltzmannMachine(
                ndim_visible=sizes["pen"] + sizes["lbl"],
                ndim_hidden=sizes["top"],
                is_top=True,
                n_labels=n_labels,
                batch_size=batch_size,
            ),
        }

        self.sizes = sizes

        self.image_size = image_size

        self.batch_size = batch_size

        self.n_gibbs_recog = 15

        self.n_gibbs_gener = 200

        self.n_gibbs_wakesleep = 5

        self.print_period = 2000

        return

    def recognize(self, true_img, true_lbl):

        """Recognize/Classify the data into label categories and calculate the accuracy

        Args:
          true_imgs: visible data shaped (number of samples, size of visible layer)
          true_lbl: true labels shaped (number of samples, size of label layer). Used only for calculating accuracy, not driving the net
        """

        n_samples = true_img.shape[0]

        vis = true_img  # visible layer gets the image data

        lbl = (
            np.ones(true_lbl.shape) / 10.0
        )  # start the net by telling you know nothing about labels

        num_labels = lbl.shape[1]

        # [TODO TASK 4.2] fix the image data in the visible layer and drive the network bottom to top. In the top RBM, run alternating Gibbs sampling \
        # and read out the labels (replace pass below and 'predicted_lbl' to your predicted labels).
        # NOTE : inferring entire train/test set may require too much compute memory (depends on your system). In that case, divide into mini-batches.

        # Drive from bottom to pen
        p_hid, _ = self.rbm_stack["vis--hid"].get_h_given_v_dir(vis)
        p_pen, _ = self.rbm_stack["hid--pen"].get_h_given_v_dir(p_hid)

        top_v = np.hstack((np.ndarray(p_pen.shape),lbl))

        # Run Gibbs sampling on top layer
        for _ in range(self.n_gibbs_recog):
            # Clamp "Image" (copy in "image" from previous rbm)
            top_v[:,:-num_labels] = p_pen
            _, top_h = self.rbm_stack["pen+lbl--top"].get_h_given_v(top_v)
            _, top_v = self.rbm_stack["pen+lbl--top"].get_v_given_h(top_h)

        predicted_lbl = top_v[:,-num_labels:]
        accuracy = 100.0 * np.mean(np.argmax(predicted_lbl, axis=1) == np.argmax(true_lbl, axis=1))
	
        print (f"accuracy = {accuracy:.5f}")

        return accuracy

    def generate(self, true_lbl):

        """Generate data from labels

        Args:
          true_lbl: true labels shaped (number of samples, size of label layer)
          name: string used for saving a video of generated visible activations
        """

        records = []

        lbl = true_lbl
        num_label = lbl.shape[1]
        
        # [TODO TASK 4.2] fix the label in the label layer and run alternating Gibbs sampling in the top RBM. From the top RBM, drive the network \
        # top to the bottom visible layer (replace 'vis' from random to your generated visible layer).

        top = self.rbm_stack["pen+lbl--top"]
        pen = self.rbm_stack["hid--pen"]
        hid = self.rbm_stack["vis--hid"]
        
        p_top_v = np.random.uniform(0,1,(lbl.shape[0], top.bias_v.shape[0]))
        top_v = sample_binary(p_top_v)
     
        for it in range(self.n_gibbs_gener):
            p_top_v[:,-num_label:] = lbl
            top_v[:,-num_label:] = lbl
     
            p_top_h, top_h = top.get_h_given_v(p_top_v)
            p_top_v, top_v = top.get_v_given_h(p_top_h)

        v = np.zeros((28,28))

        for _ in range(100):
            top_h = sample_binary(p_top_h)
            _, top_v = top.get_v_given_h(top_h)
            _, pen_v = pen.get_v_given_h_dir(top_v[:,:-num_label])
            vis, _ = hid.get_v_given_h_dir(pen_v)
            v += vis.reshape(28,28)
        
        # plt.clf()
        # plt.imshow(v)
        # plt.show(block=False)
        # plt.pause(0.01)
            
        return v

    def train_greedylayerwise(self, vis_trainset, lbl_trainset, n_iterations):

        """
        Greedy layer-wise training by stacking RBMs. This method first tries to load previous saved parameters of the entire RBM stack. 
        If not found, learns layer-by-layer (which needs to be completed) .
        Notice that once you stack more layers on top of a RBM, the weights are permanently untwined.

        Args:
          vis_trainset: visible data shaped (size of training set, size of visible layer)
          lbl_trainset: label data shaped (size of training set, size of label layer)
          n_iterations: number of iterations of learning (each iteration learns a mini-batch)
        """

        try:
            
            self.loadfromfile_rbm(loc="trained_rbm", name="vis--hid")
            self.rbm_stack["vis--hid"].untwine_weights()

            self.loadfromfile_rbm(loc="trained_rbm", name="hid--pen")
            self.rbm_stack["hid--pen"].untwine_weights()

            self.loadfromfile_rbm(loc="trained_rbm", name="pen+lbl--top")

        except IOError:

            # [TODO TASK 4.2] use CD-1 to train all RBMs greedily

            print("training vis--hid")
            cur_rbm = self.rbm_stack["vis--hid"]
            cur_rbm.cd1(vis_trainset, n_iterations) 
            self.savetofile_rbm(loc="trained_rbm", name="vis--hid")
            p_hid, _ = cur_rbm.get_h_given_v(vis_trainset)

            self.rbm_stack["vis--hid"].untwine_weights()

            print("training hid--pen")

            cur_rbm = self.rbm_stack["hid--pen"]
            cur_rbm.cd1(p_hid, n_iterations)
            self.savetofile_rbm(loc="trained_rbm", name="hid--pen")
            p_pen, _ = cur_rbm.get_h_given_v(p_hid)
            
            self.rbm_stack["hid--pen"].untwine_weights()

            print("training pen+lbl--top")
            # Concat pen's output with labels
            data_pen_lbl = np.hstack((p_pen, lbl_trainset))

            cur_rbm = self.rbm_stack["pen+lbl--top"]
            cur_rbm.cd1(data_pen_lbl, n_iterations)

            self.savetofile_rbm(loc="trained_rbm", name="pen+lbl--top")

        return

    def train_wakesleep_finetune(self, vis_trainset, lbl_trainset, n_iterations):

        """
        Wake-sleep method for learning all the parameters of network. 
        First tries to load previous saved parameters of the entire network.

        Args:
          vis_trainset: visible data shaped (size of training set, size of visible layer)
          lbl_trainset: label data shaped (size of training set, size of label layer)
          n_iterations: number of iterations of learning (each iteration learns a mini-batch)
        """

        print("\ntraining wake-sleep..")

        try:
            raise IOError
            self.loadfromfile_dbn(loc="trained_dbn", name="vis--hid")
            self.loadfromfile_dbn(loc="trained_dbn", name="hid--pen")
            self.loadfromfile_rbm(loc="trained_dbn", name="pen+lbl--top")

        except IOError:

            self.n_samples = vis_trainset.shape[0]
            num_labels = lbl_trainset.shape[1]

            vis_hid = self.rbm_stack["vis--hid"]
            hid_pen = self.rbm_stack["hid--pen"]
            penlbl_top = self.rbm_stack["pen+lbl--top"]

            self.accuracy = []

            for it in range(n_iterations):

                print("iteration=%7d" % it)

                for b_low in range(0, self.n_samples, self.batch_size):
                    print (b_low)
                    vis_batch = vis_trainset[b_low:b_low+self.batch_size]
                    lbl_batch = lbl_trainset[b_low:b_low+self.batch_size]

                    # vis -> wake_s_hid_h -> wake_s_pen_h / wake_s_top_v -> wake_s_top_h
                    # sleep_vis <- sleep_s_hid_h <- sleep_s_pen_h / sleep_s_top_v <- wake_s_top_h

                    # [TODO TASK 4.3] wake-phase : drive the network bottom to top using fixing the visible and label data.
                    wake_p_hid_h, wake_s_hid_h = vis_hid.get_h_given_v_dir(vis_batch)
                    wake_p_pen_h, wake_s_pen_h = hid_pen.get_h_given_v_dir(wake_p_hid_h)

                    wake_s_top_v = np.hstack((wake_p_pen_h, lbl_batch))
                    wake_s_top_v_0 = np.copy(wake_s_top_v)
                    
                    wake_p_top_h, wake_s_top_h = penlbl_top.get_h_given_v(wake_s_top_v)
                    wake_s_top_h_0 = np.copy(wake_s_top_h)

                    # [TODO TASK 4.3] alternating Gibbs sampling in the top RBM for k='n_gibbs_wakesleep' steps, also store neccessary information for learning this RBM.
                    for g_it in range(self.n_gibbs_wakesleep):
                        wake_p_top_v, wake_s_top_v = penlbl_top.get_v_given_h(wake_s_top_h)
                        wake_p_top_h, wake_s_top_h = penlbl_top.get_h_given_v(wake_s_top_v)


                    # [TODO TASK 4.3] sleep phase : from the activities in the top RBM, drive the network top to bottom.
                    sleep_p_pen_h, sleep_s_pen_h = wake_p_top_v[:,:-num_labels], wake_s_top_v[:,:-num_labels]
                    sleep_p_hid_h, sleep_s_hid_h = hid_pen.get_v_given_h_dir(sleep_p_pen_h)
                    sleep_p_vis, sleep_s_vis = vis_hid.get_v_given_h_dir(sleep_p_hid_h) 


                    # [TODO TASK 4.3] compute predictions : compute generative predictions from wake-phase activations, and recognize predictions from sleep-phase activations.
                    # Note that these predictions will not alter the network activations, we use them only to learn the directed connections.

                    gen_p_hid_v, _ = vis_hid.get_v_given_h_dir(wake_s_hid_h)
                    gen_p_pen_v, _ = hid_pen.get_v_given_h_dir(wake_s_pen_h)

                    rec_p_hid_h, _ = vis_hid.get_h_given_v_dir(sleep_p_vis)
                    rec_p_pen_h, _ = hid_pen.get_h_given_v_dir(sleep_p_hid_h)

                    # [TODO TASK 4.3] update generative parameters : here you will only use 'update_generate_params' method from rbm class.

                    vis_hid.update_generate_params(wake_s_hid_h, vis_batch, gen_p_hid_v)
                    hid_pen.update_generate_params(wake_s_pen_h, wake_p_hid_h, gen_p_pen_v)

                    # [TODO TASK 4.3] update parameters of top rbm : here you will only use 'update_params' method from rbm class.

                    penlbl_top.update_params(wake_s_top_v_0, wake_s_top_h_0, wake_p_top_v, wake_p_top_h)

                    # [TODO TASK 4.3] update generative parameters : here you will only use 'update_recognize_params' method from rbm class.

                    vis_hid.update_recognize_params(sleep_s_vis, sleep_p_hid_h, rec_p_hid_h)
                    hid_pen.update_recognize_params(sleep_s_hid_h, sleep_p_pen_h, rec_p_pen_h)


                    #self.recognize(vis_batch, lbl_batch)
                self.accuracy.append(self.recognize(vis_trainset, lbl_trainset))
                print (self.accuracy[-1])


            self.savetofile_dbn(loc="trained_dbn", name="vis--hid")
            self.savetofile_dbn(loc="trained_dbn", name="hid--pen")
            self.savetofile_rbm(loc="trained_dbn", name="pen+lbl--top")

        return

    def loadfromfile_rbm(self, loc, name):

        self.rbm_stack[name].weigt_vhh = np.load(
            "%s/rbm.%s.weight_vh.npy" % (loc, name)
        )
        self.rbm_stack[name].bias_v = np.load("%s/rbm.%s.bias_v.npy" % (loc, name))
        self.rbm_stack[name].bias_h = np.load("%s/rbm.%s.bias_h.npy" % (loc, name))
        print("loaded rbm[%s] from %s" % (name, loc))
        return

    def savetofile_rbm(self, loc, name):

        np.save("%s/rbm.%s.weight_vh" % (loc, name), self.rbm_stack[name].weight_vh)
        np.save("%s/rbm.%s.bias_v" % (loc, name), self.rbm_stack[name].bias_v)
        np.save("%s/rbm.%s.bias_h" % (loc, name), self.rbm_stack[name].bias_h)
        return

    def loadfromfile_dbn(self, loc, name):

        self.rbm_stack[name].weight_v_to_h = np.load(
            "%s/dbn.%s.weight_v_to_h.npy" % (loc, name)
        )
        self.rbm_stack[name].weight_h_to_v = np.load(
            "%s/dbn.%s.weight_h_to_v.npy" % (loc, name)
        )
        self.rbm_stack[name].bias_v = np.load("%s/dbn.%s.bias_v.npy" % (loc, name))
        self.rbm_stack[name].bias_h = np.load("%s/dbn.%s.bias_h.npy" % (loc, name))
        print("loaded rbm[%s] from %s" % (name, loc))
        return

    def savetofile_dbn(self, loc, name):

        np.save(
            "%s/dbn.%s.weight_v_to_h" % (loc, name), self.rbm_stack[name].weight_v_to_h
        )
        np.save(
            "%s/dbn.%s.weight_h_to_v" % (loc, name), self.rbm_stack[name].weight_h_to_v
        )
        np.save("%s/dbn.%s.bias_v" % (loc, name), self.rbm_stack[name].bias_v)
        np.save("%s/dbn.%s.bias_h" % (loc, name), self.rbm_stack[name].bias_h)
        return
