class Data:
	@classmethod
	def from_data(self, cls, data):
		dataset = {}
		for datapoint in data:
			data_object = cls(datapoint)
			dataset[repr(data_object)] = data_object
		return dataset
