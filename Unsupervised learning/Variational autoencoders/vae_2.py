import torch
from data_generator import train_data_size, test_data_size, filename

from torch.autograd import Variable
import numpy as np
import torch.nn.functional as F
import torchvision
from torchvision import transforms
import torch.optim as optim
from torch import nn
import matplotlib.pyplot as plt
import csv
import random

#device = torch.device("cuda")

import os


model2_file = "model2_save"

data_size = train_data_size + test_data_size

device = torch.device("cuda")
random.seed(100)

input_dim = 2
latent_dim = 1

epochs = 50

from torch.distributions import uniform

distribution = uniform.Uniform(torch.Tensor([0.5]),torch.Tensor([100.0]))



class VAE(nn.Module):
    def __init__(self):
        super(VAE, self).__init__()

        self.fc1 = nn.Linear(input_dim, 400)
        self.fc21 = nn.Linear(400, latent_dim)
        self.fc22 = nn.Linear(400, latent_dim)
        self.fc3 = nn.Linear(latent_dim, 200)
        self.fc4 = nn.Linear(200, input_dim)

    def encode(self, x):
        h1 = F.relu(self.fc1(x))
        return self.fc21(h1), self.fc22(h1)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5*logvar)
        eps = torch.randn_like(std)
        return eps.mul(std).add_(mu)

    def decode(self, z):
        h3 = F.relu(self.fc3(z))
        return torch.sigmoid(self.fc4(h3))


    def forward(self, x):
        mu, logvar = self.encode(x.view(-1, 2))
        z = self.reparameterize(mu, logvar)
        return z, self.decode(z), mu, logvar



# Reconstruction + KL divergence losses summed over all elements and batch
def loss_function(recon_x, x, mu, logvar):
    BCE = F.binary_cross_entropy(recon_x, x.view(-1, 2), reduction='sum')

    # see Appendix B from VAE paper:
    # Kingma and Welling. Auto-Encoding Variational Bayes. ICLR, 2014
    # https://arxiv.org/abs/1312.6114
    # 0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

    return BCE + KLD




if __name__ == '__main__':

    if os.path.exists(model2_file):
        os.remove(model2_file)
    else:
        print("The file does not exist. New file created")

    #print(input1, input2, input3, tolearn)

    #input_dim = 28 * 28
    #batch_size = 32
    #transform = transforms.Compose([transforms.ToTensor()])
    #mnist = torchvision.datasets.MNIST('./', download=True, transform=transform)
    #dataloader = torch.utils.data.DataLoader(mnist, batch_size=batch_size, shuffle=True, num_workers=2)

    #print('Number of samples: ', len(mnist))

    input_dim = 2*1

    # Load data from file

    inputs1, inputs2, tolearn = [], [], []

    for line in open(filename, "r"):
        values = [float(s) for s in line.split()]
        # Normalize Data
        normalizing_factor = 150
        inputs1.append([values[0] / normalizing_factor, values[1] / normalizing_factor])
        inputs2.append([values[2] / normalizing_factor, values[3] / normalizing_factor])
        tolearn.append(values[4] / normalizing_factor)

    train_data = inputs2[0:train_data_size]
    test_data = inputs2[train_data_size: data_size]

    # dataloader = torch.utils.data.DataLoader(mnist, batch_size=batch_size, shuffle=True, num_workers=2)

    # print('Number of samples: ', len(mnist))

    #encoder = Encoder(input_dim, 100, 100)  # dim_in, hidden_layers, dim_out
    #decoder = Decoder(latent_dim, 100, input_dim)

    #encoder = encoder.cuda()
    #decoder = decoder.cuda()

    #criterion = nn.MSELoss()
    #optimizer = optim.Adam(vae.parameters(), lr=0.0001)
    l = None

    model = VAE().to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    print("Training for 1st operation....")
    for epoch in range(epochs):
        model.train()
        train_loss = 0

        # shuffle the data
        #print("TRAINING--------------", inputs1[0:train_data_size])
        np.random.shuffle(train_data)

        for i in range(len(train_data)):
            #a = distribution.sample(torch.Size([1]))
            #a1 = input1[i]
            #out1 = input2[i]

            # Normalize data points
            #normalize_a1 = a1
            #normalize_out1 = out1
            #c = torch.cat((a, out1), 0)
            #inputs = c

            #inputs1 = torch.tensor([normalize_a1, normalize_out1])



            input = train_data[i]
            input = torch.tensor(input)
            input = input.to(device)

            optimizer.zero_grad()

            latent_rep, recon_batch, mu, logvar = model(input)
            #latent_space, dec = vae(input1)
            loss = loss_function(recon_batch, input, mu, logvar)

            loss.backward()
            train_loss += loss.item()
            optimizer.step()


        #print('====> Epoch: {} Average loss: {:.4f}'.format(epoch, train_loss / train_data_size))

        if epoch % epochs == 0:
            model2 = model
            with open(model2_file, 'wb') as f:
                torch.save(model2.state_dict(), f)
            #print("Mean", vae.z_mean.data, "Sigma", vae.z_sigma.data)

        # print("Our model: \n\n", vae, '\n')
        # print("The state dict keys: \n\n", vae.state_dict().keys())


        else:# when training is done, carry on with Testing/Validation/Inference
            # shuffle the data
            #print("TESTING--------------", inputs1[train_data_size: test_data_size - 1])

            np.random.shuffle(test_data)
            print("TESTING DATA: ", test_data)
            model.eval()
            test_loss = 0
            accuracy = 0

            # Turn off gradients for validation as it saves memory and computation
            with torch.no_grad():
                for i in range(len(test_data)):
                    # Flatten Images images pixels to a vector
                    input = test_data[i]
                    input = torch.tensor(input)
                    input = input.to(device)
                    latent_rep, recon_batch, mu, logvar = model(input)

                    test_loss += loss_function(recon_batch, input, mu, logvar).item()

            print("INPUT: ", input, "OUTPUT: ", recon_batch, "LATENT REP: ", latent_rep)
            print("====> Epoch: {}/{}.. ".format(epoch + 1, epochs),
                  "Training Loss: {:.3f}.. ".format(train_loss / train_data_size),
                  "Test Loss: {:.3f}.. ".format(test_loss / test_data_size),
                  #"Test Accuracy: {:.3f}.. ".format(accuracy / test_data_size)
                  )
