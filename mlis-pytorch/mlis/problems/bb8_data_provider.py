import torch
from ..core.case_data import CaseData

# There are 2 languages.
class Language:
    def __init__(self, states_count, letters_count):
        self.states_count = states_count
        with torch.no_grad():
            self.state_to_state_prob = torch.FloatTensor(states_count, states_count).uniform_()
            self.state_to_state_prob = self.state_to_state_prob/torch.sum(self.state_to_state_prob, dim=1).view(-1,1)
            self.state_to_state_cum_prob = torch.cumsum(self.state_to_state_prob, dim=1)

    def balance(self, sentences):
        letters_id, counts = torch.unique(sentences.view(-1), sorted=True, return_counts=True)
        perm = torch.randperm(letters_id.size(0))
        letters_id = letters_id[perm]
        counts = counts[perm]
        total = counts.sum().item()
        x = torch.BoolTensor(total+1).zero_()
        x[0] = 1
        xs = [x]
        for letter_id, count in zip(letters_id, counts):
            cc = count.item()
            nx = xs[-1].clone()
            nx[cc:][xs[-1][:-cc]] = 1
            xs.append(nx)
        best_balance = total//2
        while xs[-1][best_balance].item() == 0:
            best_balance -= 1
        #if best_balance != total//2:
        #    print("UNBALANCED")
        current_balance = best_balance
        balance_set = [False for _ in range(letters_id.size(0))]
        last_ind = len(xs)-1
        while current_balance != 0:
            while xs[last_ind-1][current_balance].item() == 1:
                last_ind -= 1
            balance_set[last_ind-1] = True
            current_balance -= counts[last_ind-1].item()
        b_sentences = sentences.clone()
        self.state_to_state_letter = self.state_to_state_letter.view(-1)
        for ind, set_id in enumerate(balance_set):
            val = 0
            if set_id:
                val = 1
            b_sentences[sentences == letters_id[ind]] = val
            self.state_to_state_letter[letters_id[ind]] = val
        assert b_sentences.view(-1).sum() == best_balance
        self.state_to_state_letter = self.state_to_state_letter.view(self.states_count, self.states_count)
        return b_sentences

    def gen(self, count, length):
        with torch.no_grad():
            self.state_to_state_letter = torch.arange(self.states_count*self.states_count).view(self.states_count, self.states_count)
            #self.state_to_state_letter.random_(0,2)
            sentences = torch.LongTensor(count, length)
            states = torch.LongTensor(count).random_(0, self.states_count)
            for i in range(length):
                res = torch.FloatTensor(count).uniform_()
                probs = self.state_to_state_cum_prob[states]
                next_states = self.states_count-(res.view(-1,1) < probs).sum(dim=1)
                next_states = next_states.clamp(max=self.states_count-1)
                letters_ind = self.state_to_state_letter[states, next_states]
                sentences[:,i] = letters_ind
                states = next_states
            sentences = self.balance(sentences)
            return sentences

    def calc_probs(self, sentences):
        size = sentences.size(0)
        states_count = self.state_to_state_prob.size(0)
        length = sentences.size(1)
        with torch.no_grad():
            state_to_prob = torch.FloatTensor(size, states_count).double()
            state_to_prob[:,:] = 1.0
            for i in range(length):
                letters = sentences[:,i]
                s1 = self.state_to_state_letter.size()
                s2 = letters.size()
                sf = s2+s1

                t1 = self.state_to_state_letter.view((1,)+s1).expand(sf)
                t2 = letters.view(s2+(1,1)).expand(sf)
                t3 = self.state_to_state_prob.view((1,)+s1).expand(sf).double()
                t4 = (t1 == t2).double()
                t5 = torch.mul(t3, t4)
                t6 = state_to_prob
                next_state_to_prob = torch.matmul(t6.view(t6.size(0), 1, t6.size(1)), t5).view_as(t6)
                state_to_prob = next_state_to_prob
            return state_to_prob.sum(dim=1)

class DataProvider:
    def create_data(self, data_size, length, states_count, letters_count, seed):
        while True:
            torch.manual_seed(seed)
            languages = [Language(states_count, letters_count), Language(states_count, letters_count)]
            data_size_per_lang = data_size//len(languages)
            datas = []
            targets = []
            for ind, lan in enumerate(languages):
                datas.append(lan.gen(data_size_per_lang, length))
                t = torch.LongTensor(data_size_per_lang)
                t[:] = ind
                targets.append(t)
            bad_count = 0
            good_count = 0
            for ind, data in enumerate(datas):
                probs = [lan.calc_probs(data) for lan in languages]
                bad_count += (probs[ind] <= probs[1-ind]).long().sum().item()
                good_count += (probs[ind] > probs[1-ind]).long().sum().item()
            best_prob = good_count/(bad_count+good_count)
            if best_prob > 0.95:
                break
            print("Low best prob = {}, seed = {}".format(best_prob, seed))
            seed += 1

        data = torch.cat(datas, dim=0)
        target = torch.cat(targets, dim=0)
        perm = torch.randperm(data.size(0))
        data = data[perm]
        target = target[perm]
        return (data, target.view(-1, 1).float(), best_prob)

    def create_case_data(self, config):
        case_data = CaseData()
        # correct seed help generate data faster
        seed = config['seed']
        data_size = config['dataSize']
        length = config['length']
        states_count = config['statesCount']
        letters_count = 2
        data, target, best_prob = self.create_data(2*data_size, length, states_count, letters_count, seed)
        print('Best prob = {}'.format(best_prob))

        case_data.set_train_data((data[:data_size], target[:data_size]))
        case_data.set_test_data((data[data_size:], target[data_size:]))
        return case_data